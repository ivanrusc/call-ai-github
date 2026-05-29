#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

load_dotenv("/srv/call-ai/.env")

BASE_DIR = Path(os.getenv("CALL_AI_BASE", "/srv/call-ai"))
AUDIO_IN = BASE_DIR / "audio_in"

DB = {
    "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB", "call_ai"),
    "user": os.getenv("POSTGRES_USER", "call_ai"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".wma"
}

ASSISTENCIA_VALUE = os.getenv("ASSISTENCIA_VALUE", "34930185139")


def detect_service_type(filename: str) -> str:
    if ASSISTENCIA_VALUE in filename:
        return "assistencia"
    return "oficina"


def detect_call_date(path: Path):
    """
    Busca una carpeta amb format YYYY-MM-DD dins la ruta relativa a audio_in.
    Exemple:
      /srv/call-ai/audio_in/2026-05-29/trucada.mp3 -> 2026-05-29
    """
    try:
        rel = path.relative_to(AUDIO_IN)
    except ValueError:
        return None

    for part in rel.parts[:-1]:
        if re.match(r"^\d{4}-\d{2}-\d{2}$", part):
            try:
                return datetime.strptime(part, "%Y-%m-%d").date()
            except ValueError:
                return None

    return None


def main():
    if len(sys.argv) != 2:
        print("Ús:")
        print("  register_audio_files.py BATCH_ID")
        print()
        print("Exemple:")
        print("  register_audio_files.py 1")
        sys.exit(1)

    batch_id = int(sys.argv[1])

    files = [
        p for p in AUDIO_IN.rglob("*")
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    ]

    if not files:
        print(f"No he trobat àudios a: {AUDIO_IN}")
        sys.exit(0)

    conn = psycopg2.connect(**DB)
    conn.autocommit = False

    inserted = 0
    updated = 0

    try:
        with conn.cursor() as cur:
            for path in sorted(files):
                original_path = str(path)
                original_filename = path.name
                service_type = detect_service_type(original_filename)
                call_date = detect_call_date(path)

                cur.execute(
                    """
                    SELECT id
                    FROM calls
                    WHERE original_path = %s
                    LIMIT 1
                    """,
                    (original_path,)
                )

                exists = cur.fetchone()

                if exists:
                    call_id = exists[0]

                    cur.execute(
                        """
                        UPDATE calls
                        SET batch_id = %s,
                            service_type = %s,
                            call_date = %s,
                            updated_at = now()
                        WHERE id = %s
                        """,
                        (batch_id, service_type, call_date, call_id)
                    )

                    updated += 1
                    continue

                cur.execute(
                    """
                    INSERT INTO calls
                    (
                        batch_id,
                        original_filename,
                        original_path,
                        service_type,
                        call_date,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s, 'imported')
                    """,
                    (
                        batch_id,
                        original_filename,
                        original_path,
                        service_type,
                        call_date
                    )
                )

                inserted += 1

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        sys.exit(1)

    finally:
        conn.close()

    print("==========================================")
    print(f"Carpeta entrada: {AUDIO_IN}")
    print(f"Fitxers trobats: {len(files)}")
    print(f"Afegits BBDD:    {inserted}")
    print(f"Actualitzats:    {updated}")
    print("==========================================")


if __name__ == "__main__":
    main()
