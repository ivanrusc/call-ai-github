#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from faster_whisper import WhisperModel


load_dotenv("/srv/call-ai/.env")

BASE_DIR = Path(os.getenv("CALL_AI_BASE", "/srv/call-ai"))
TMP_WAV_DIR = BASE_DIR / "tmp_wav"
TRANSCRIPTS_DIR = BASE_DIR / "transcripts"
LOGS_DIR = BASE_DIR / "logs"

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "auto")
WHISPER_VAD = os.getenv("WHISPER_VAD", "true").lower() == "true"

DB = {
    "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB", "call_ai"),
    "user": os.getenv("POSTGRES_USER", "call_ai"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

TMP_WAV_DIR.mkdir(parents=True, exist_ok=True)
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def seconds_to_srt_time(seconds: float) -> str:
    millis = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02},{millis:03}"


def db_connect():
    return psycopg2.connect(**DB)


def update_call_status(conn, call_id: int, status: str, error_message=None):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE calls
            SET status = %s,
                error_message = %s,
                updated_at = now()
            WHERE id = %s
            """,
            (status, error_message, call_id),
        )
    conn.commit()


def get_call(conn, call_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                id,
                original_filename,
                original_path,
                service_type,
                call_date,
                status
            FROM calls
            WHERE id = %s
            """,
            (call_id,),
        )
        return cur.fetchone()


def convert_to_wav(input_file: Path, wav_file: Path):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_file),
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(wav_file),
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )


def save_transcript_to_db(
    conn,
    call_id: int,
    language,
    language_probability,
    transcript_text,
    txt_path,
    srt_path,
    transcript_json_path,
    whisper_model,
    processing_seconds,
    duration_seconds,
):
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM transcripts
            WHERE call_id = %s
            """,
            (call_id,),
        )

        cur.execute(
            """
            INSERT INTO transcripts
            (
                call_id,
                language,
                language_probability,
                transcript_text,
                srt_path,
                transcript_json_path,
                whisper_model,
                processing_seconds
            )
            VALUES
            (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                call_id,
                language,
                language_probability,
                transcript_text,
                str(srt_path),
                str(transcript_json_path),
                whisper_model,
                processing_seconds,
            ),
        )

        cur.execute(
            """
            UPDATE calls
            SET status = 'transcribed',
                duration_seconds = %s,
                wav_temp_path = NULL,
                error_message = NULL,
                updated_at = now()
            WHERE id = %s
            """,
            (duration_seconds, call_id),
        )

    conn.commit()


def main():
    if len(sys.argv) != 2:
        print("Ús:")
        print("  transcribe_call.py CALL_ID")
        print()
        print("Exemple:")
        print("  transcribe_call.py 1")
        sys.exit(1)

    call_id = int(sys.argv[1])

    conn = db_connect()

    row = get_call(conn, call_id)

    if not row:
        print(f"ERROR: No existeix call_id={call_id}")
        sys.exit(1)

    (
        db_call_id,
        original_filename,
        original_path,
        service_type,
        call_date,
        status,
    ) = row

    input_file = Path(original_path)

    if not input_file.exists():
        update_call_status(conn, call_id, "error", f"No existeix el fitxer: {input_file}")
        print(f"ERROR: No existeix el fitxer: {input_file}")
        sys.exit(1)

    safe_name = input_file.stem.replace(" ", "_")
    wav_file = TMP_WAV_DIR / f"{call_id}_{safe_name}.wav"
    txt_file = TRANSCRIPTS_DIR / f"{call_id}_{safe_name}.txt"
    srt_file = TRANSCRIPTS_DIR / f"{call_id}_{safe_name}.srt"
    json_file = TRANSCRIPTS_DIR / f"{call_id}_{safe_name}.transcript.json"

    print("==========================================")
    print(f" CALL_ID:        {call_id}")
    print(f" Fitxer entrada: {input_file}")
    print(f" Tipus servei:   {service_type}")
    print(f" Data trucada:   {call_date}")
    print(f" Estat actual:   {status}")
    print(f" Model Whisper:  {WHISPER_MODEL}")
    print(f" Device:         {WHISPER_DEVICE}")
    print(f" Compute type:   {WHISPER_COMPUTE_TYPE}")
    print(f" Language:       {WHISPER_LANGUAGE}")
    print(f" VAD filter:     {WHISPER_VAD}")
    print("==========================================")

    started = time.time()

    try:
        update_call_status(conn, call_id, "transcribing")

        print("[1/4] Convertint àudio a WAV temporal...")
        convert_to_wav(input_file, wav_file)

        print("[2/4] Carregant model Whisper...")
        model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
        )

        print("[3/4] Transcrivint...")

        transcribe_options = {
            "beam_size": 5,
            "vad_filter": WHISPER_VAD,
            "condition_on_previous_text": False,
            "initial_prompt": (
                "Aquesta és una trucada d'atenció al client de Som Mobilitat. "
                "La conversa pot ser en català o castellà. "
                "Transcriu literalment el que es diu. No tradueixis. "
                "Poden aparèixer paraules com reserva, vehicle, punt de càrrega, "
                "assistència, oficina, soci, incidència."
            ),
        }

        if WHISPER_LANGUAGE and WHISPER_LANGUAGE.lower() != "auto":
            transcribe_options["language"] = WHISPER_LANGUAGE

        segments, info = model.transcribe(
            str(wav_file),
            **transcribe_options,
        )

        all_segments = []
        text_parts = []

        with srt_file.open("w", encoding="utf-8") as srt:
            for idx, segment in enumerate(segments, start=1):
                text = segment.text.strip()

                if not text:
                    continue

                all_segments.append(
                    {
                        "start": segment.start,
                        "end": segment.end,
                        "text": text,
                    }
                )

                text_parts.append(text)

                srt.write(f"{idx}\n")
                srt.write(
                    f"{seconds_to_srt_time(segment.start)} --> "
                    f"{seconds_to_srt_time(segment.end)}\n"
                )
                srt.write(f"{text}\n\n")

        transcript_text = "\n".join(text_parts).strip()
        txt_file.write_text(transcript_text, encoding="utf-8")

        elapsed = round(time.time() - started, 2)

        metadata = {
            "call_id": call_id,
            "original_filename": original_filename,
            "original_path": str(input_file),
            "txt_path": str(txt_file),
            "srt_path": str(srt_file),
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "duration_after_vad": getattr(info, "duration_after_vad", None),
            "whisper_model": WHISPER_MODEL,
            "device": WHISPER_DEVICE,
            "compute_type": WHISPER_COMPUTE_TYPE,
            "configured_language": WHISPER_LANGUAGE,
            "vad_filter": WHISPER_VAD,
            "processing_seconds": elapsed,
            "segments": all_segments,
        }

        json_file.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print("[4/4] Guardant transcripció a PostgreSQL...")

        save_transcript_to_db(
            conn=conn,
            call_id=call_id,
            language=info.language,
            language_probability=info.language_probability,
            transcript_text=transcript_text,
            txt_path=txt_file,
            srt_path=srt_file,
            transcript_json_path=json_file,
            whisper_model=WHISPER_MODEL,
            processing_seconds=elapsed,
            duration_seconds=info.duration,
        )

        if wav_file.exists():
            wav_file.unlink()

        with (LOGS_DIR / "transcribe_call.log").open("a", encoding="utf-8") as log:
            log.write(
                f"OK call_id={call_id} "
                f"file={original_filename} "
                f"seconds={elapsed} "
                f"lang={info.language}\n"
            )

        print("==========================================")
        print("Fet.")
        print(f"TXT:  {txt_file}")
        print(f"SRT:  {srt_file}")
        print(f"JSON: {json_file}")
        print(f"Idioma detectat: {info.language}")
        print(f"Durada àudio: {info.duration} segons")
        print(f"Temps procés: {elapsed} segons")
        print("Estat BBDD: transcribed")
        print("==========================================")

    except subprocess.CalledProcessError:
        msg = "Error convertint àudio amb ffmpeg"
        update_call_status(conn, call_id, "error", msg)
        print(f"ERROR: {msg}")
        sys.exit(1)

    except Exception as e:
        msg = str(e)
        update_call_status(conn, call_id, "error", msg)
        print("ERROR:")
        print(msg)
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
