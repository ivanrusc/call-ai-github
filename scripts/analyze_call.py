#!/usr/bin/env python3
import os
import re
import sys
import json
import time
import unicodedata
from pathlib import Path

import requests
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv


load_dotenv("/srv/call-ai/.env")

BASE_DIR = Path(os.getenv("CALL_AI_BASE", "/srv/call-ai"))
ANALYSIS_DIR = BASE_DIR / "analysis"
LOGS_DIR = BASE_DIR / "logs"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

DB = {
    "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB", "call_ai"),
    "user": os.getenv("POSTGRES_USER", "call_ai"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def normalize_text(value):
    if value is None:
        return None

    value = str(value).strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_identifier(identifier_type, value):
    if not value:
        return None

    v = str(value).strip().lower()

    if identifier_type in ("telefon", "phone"):
        v = re.sub(r"\D+", "", v)
        return v

    if identifier_type in ("dni", "dni_nie", "nie"):
        v = re.sub(r"[^0-9a-zA-Z]+", "", v).lower()
        return v

    if identifier_type == "email":
        return v

    return normalize_text(v)


def should_keep_identifier(identifier_type, value):
    """
    Evita guardar falsos identificadors.
    Exemple: "30 euros" no és un número de reserva.
    """
    if not identifier_type or not value:
        return False

    t = normalize_text(identifier_type).replace(" ", "_")
    v = str(value).strip().lower()

    # No guardem imports com si fossin identificadors
    if re.search(r"\b(euro|euros|€|eur)\b", v):
        return False

    # No guardem quantitats monetàries com a número de reserva/client/soci
    if t in ("numero_reserva", "numero_client", "numero_soci"):
        only_digits = re.sub(r"\D+", "", v)

        # Si només té 1-3 dígits, probablement és import, hora, minut, etc.
        if len(only_digits) < 4:
            return False

    # Telèfon: mínim 9 dígits
    if t == "telefon":
        digits = re.sub(r"\D+", "", v)
        return len(digits) >= 9

    # DNI/NIE: mínim 8 caràcters alfanumèrics
    if t == "dni_nie":
        clean = re.sub(r"[^0-9a-zA-Z]+", "", v)
        return len(clean) >= 8

    # Email ha de tenir @ i punt
    if t == "email":
        return "@" in v and "." in v

    return True


def clean_model_response(text):
    """
    Neteja respostes del model:
    - elimina <think>...</think>
    - elimina ```json
    - intenta extreure només el JSON
    """
    if not text:
        return ""

    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```json", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"^```", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    return text.strip()


def db_connect():
    return psycopg2.connect(**DB)


def update_call_status(conn, call_id, status, error_message=None):
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


def get_call_with_transcript(conn, call_id):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                c.id,
                c.original_filename,
                c.original_path,
                c.service_type,
                c.call_date,
                c.status,
                t.transcript_text,
                t.language
            FROM calls c
            JOIN transcripts t ON t.call_id = c.id
            WHERE c.id = %s
            """,
            (call_id,),
        )
        return cur.fetchone()


def call_ollama(payload):
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        timeout=600,
    )
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


def build_prompt(original_filename, service_type, call_date, transcript_text):
    system_prompt = """
Ets un analista professional de trucades d'atenció al client.
Analitzes trucades de Som Mobilitat.

Objectiu:
- Extreure motius de trucada.
- Separar consultes diferents dins una mateixa trucada.
- Detectar resolució.
- Detectar si és emergència.
- Detectar si és assistència o oficina, però el tipus ja ve donat pel sistema.
- Detectar si hi ha reserva i si s'ha pogut finalitzar.
- Agrupar motius semblants.
- Detectar dades identificatives.
- Generar paraules clau útils per cerques.

Important:
- La transcripció pot tenir errors de STT.
- Interpreta amb prudència.
- No inventis dades.
- Si no estàs segur, posa confiança baixa.
- Respon només en JSON vàlid.
- No facis markdown.
- No afegeixis text fora del JSON.
"""

    user_prompt = f"""
Dades de la trucada:
- filename: {original_filename}
- service_type: {service_type}
- call_date: {call_date}

Regles fixes:
- service_type ja ve calculat pel sistema.
- Si service_type és "assistencia", tota consulta és d'assistència.
- Si service_type és "oficina", tota consulta és d'oficina.
- Separa sempre assistència i oficina mitjançant service_type.
- Si en una trucada hi ha dues consultes diferents, crea dues entrades dins "consultes".
- Si no ha pogut finalitzar una reserva, indica el motiu.
- Si el problema de reserva és amb el punt de càrrega, marca es_fallada_punt_carrega = true.
- Agrupa motius semblants amb un nom estable dins "motiu_agrupat".
- Detecta dades identificatives només si apareixen clarament a la transcripció.
- No consideris imports, preus, hores o durades com a numero_reserva.
- Exemple: "30 euros" NO és numero_reserva.
- Exemple: "de 5 a 8 de la tarda" NO és numero_reserva.
- Un numero_reserva ha de semblar un codi, referència o identificador de reserva.

Motius agrupats recomanats:
- Incidència punt de càrrega
- Reserva no finalitzada
- Dubte reserva
- Modificació reserva
- Cancel·lació reserva
- Vehicle no disponible
- Vehicle no obre
- Vehicle no arrenca
- Dubte facturació
- Pagament / targeta
- Alta usuari / soci
- Baixa / cancel·lació servei
- Canvi dades usuari
- Informació comercial
- Incidència app
- Incidència web
- Emergència amb vehicle
- Objecte perdut
- Altres

Resolucio ha de ser una de:
- resolta
- no resolta
- pendent
- transferida
- informativa
- desconeguda

identifier_type pot ser:
- nom
- cognoms
- nom_complet
- dni_nie
- telefon
- email
- matricula
- adreca
- numero_soci
- numero_client
- numero_reserva
- altre

Retorna exactament aquest JSON:

{{
  "resum_general": "",
  "idioma": "",
  "transcripcio_anonimitzada": "",
  "consultes": [
    {{
      "consulta_num": 1,
      "motiu_original": "",
      "motiu_agrupat": "",
      "resolucio": "",
      "es_emergencia": false,
      "es_reserva": false,
      "reserva_finalitzada": null,
      "motiu_reserva_no_finalitzada": "",
      "es_fallada_punt_carrega": false,
      "accio_recomanada": "",
      "confianca_classificacio": 0.0,
      "paraules_clau": []
    }}
  ],
  "identificadors_detectats": [
    {{
      "identifier_type": "",
      "identifier_value": "",
      "confidence": 0.0,
      "context_fragment": ""
    }}
  ]
}}

Transcripció:
---
{transcript_text}
---
"""

    return system_prompt.strip(), user_prompt.strip()


def save_analysis(conn, call_id, service_type, call_date, parsed, processing_seconds):
    with conn.cursor() as cur:
        # Esborrem anàlisi anterior per poder reprocessar la trucada
        cur.execute("DELETE FROM call_identifiers WHERE call_id = %s", (call_id,))
        cur.execute("DELETE FROM call_keywords WHERE call_id = %s", (call_id,))
        cur.execute("DELETE FROM call_motives WHERE call_id = %s", (call_id,))
        cur.execute("DELETE FROM call_analysis WHERE call_id = %s", (call_id,))

        cur.execute(
            """
            INSERT INTO call_analysis
            (
                call_id,
                resum_general,
                idioma,
                model,
                ollama_url,
                processing_seconds,
                raw_json
            )
            VALUES
            (
                %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                call_id,
                parsed.get("resum_general", ""),
                parsed.get("idioma", ""),
                OLLAMA_MODEL,
                OLLAMA_URL,
                processing_seconds,
                Json(parsed),
            ),
        )

        redacted = parsed.get("transcripcio_anonimitzada")
        if redacted:
            cur.execute(
                """
                UPDATE transcripts
                SET transcript_text_redacted = %s
                WHERE call_id = %s
                """,
                (redacted, call_id),
            )

        consultes = parsed.get("consultes", [])
        if not isinstance(consultes, list):
            consultes = []

        for idx, item in enumerate(consultes, start=1):
            if not isinstance(item, dict):
                continue

            consulta_num = item.get("consulta_num") or idx
            motiu_original = item.get("motiu_original") or "No especificat"
            motiu_agrupat = item.get("motiu_agrupat") or motiu_original

            cur.execute(
                """
                INSERT INTO call_motives
                (
                    call_id,
                    service_type,
                    call_date,
                    consulta_num,
                    motiu_original,
                    motiu_agrupat,
                    resolucio,
                    es_emergencia,
                    es_reserva,
                    reserva_finalitzada,
                    motiu_reserva_no_finalitzada,
                    es_fallada_punt_carrega,
                    accio_recomanada,
                    confianca_classificacio,
                    raw_item
                )
                VALUES
                (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id
                """,
                (
                    call_id,
                    service_type,
                    call_date,
                    consulta_num,
                    motiu_original,
                    motiu_agrupat,
                    item.get("resolucio"),
                    bool(item.get("es_emergencia", False)),
                    bool(item.get("es_reserva", False)),
                    item.get("reserva_finalitzada"),
                    item.get("motiu_reserva_no_finalitzada"),
                    bool(item.get("es_fallada_punt_carrega", False)),
                    item.get("accio_recomanada"),
                    item.get("confianca_classificacio"),
                    Json(item),
                ),
            )

            motive_id = cur.fetchone()[0]

            keywords = item.get("paraules_clau", [])
            if isinstance(keywords, list):
                for kw in keywords:
                    kw = str(kw).strip()
                    if not kw:
                        continue

                    cur.execute(
                        """
                        INSERT INTO call_keywords
                        (
                            call_id,
                            motive_id,
                            service_type,
                            call_date,
                            keyword,
                            keyword_normalized
                        )
                        VALUES
                        (
                            %s, %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            call_id,
                            motive_id,
                            service_type,
                            call_date,
                            kw,
                            normalize_text(kw),
                        ),
                    )

        identificadors = parsed.get("identificadors_detectats", [])
        if not isinstance(identificadors, list):
            identificadors = []

        for ident in identificadors:
            if not isinstance(ident, dict):
                continue

            identifier_type = ident.get("identifier_type")
            identifier_value = ident.get("identifier_value")

            if not identifier_type or not identifier_value:
                continue

            if not should_keep_identifier(identifier_type, identifier_value):
                continue

            identifier_type = normalize_text(identifier_type).replace(" ", "_")
            identifier_value = str(identifier_value).strip()
            identifier_value_normalized = normalize_identifier(
                identifier_type,
                identifier_value,
            )

            cur.execute(
                """
                INSERT INTO call_identifiers
                (
                    call_id,
                    motive_id,
                    service_type,
                    call_date,
                    identifier_type,
                    identifier_value,
                    identifier_value_normalized,
                    confidence,
                    context_fragment
                )
                VALUES
                (
                    %s, NULL, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    call_id,
                    service_type,
                    call_date,
                    identifier_type,
                    identifier_value,
                    identifier_value_normalized,
                    ident.get("confidence"),
                    ident.get("context_fragment"),
                ),
            )

        cur.execute(
            """
            UPDATE calls
            SET status = 'analyzed',
                error_message = NULL,
                updated_at = now()
            WHERE id = %s
            """,
            (call_id,),
        )

    conn.commit()


def main():
    if len(sys.argv) != 2:
        print("Ús:")
        print("  analyze_call.py CALL_ID")
        print()
        print("Exemple:")
        print("  analyze_call.py 1")
        sys.exit(1)

    call_id = int(sys.argv[1])
    conn = db_connect()

    row = get_call_with_transcript(conn, call_id)

    if not row:
        print(f"ERROR: No trobo la trucada transcrita call_id={call_id}")
        print("Comprova que la trucada tingui entrada a transcripts.")
        sys.exit(1)

    (
        db_call_id,
        original_filename,
        original_path,
        service_type,
        call_date,
        status,
        transcript_text,
        transcript_language,
    ) = row

    print("==========================================")
    print(f" CALL_ID:        {call_id}")
    print(f" Fitxer:         {original_filename}")
    print(f" Tipus servei:   {service_type}")
    print(f" Data trucada:   {call_date}")
    print(f" Estat actual:   {status}")
    print(f" Ollama URL:     {OLLAMA_URL}")
    print(f" Model:          {OLLAMA_MODEL}")
    print("==========================================")

    started = time.time()

    try:
        update_call_status(conn, call_id, "analyzing")

        system_prompt, user_prompt = build_prompt(
            original_filename=original_filename,
            service_type=service_type,
            call_date=call_date,
            transcript_text=transcript_text,
        )

        payload = {
            "model": OLLAMA_MODEL,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "options": {
                "temperature": 0.1,
                "top_p": 0.8,
            },
        }

        print("[1/3] Enviant transcripció a Ollama...")
        raw_response = call_ollama(payload)

        safe_name = Path(original_filename).stem.replace(" ", "_")
        raw_file = ANALYSIS_DIR / f"{call_id}_{safe_name}.raw.txt"
        json_file = ANALYSIS_DIR / f"{call_id}_{safe_name}.analysis.json"

        raw_file.write_text(raw_response, encoding="utf-8")

        print("[2/3] Validant JSON...")
        cleaned = clean_model_response(raw_response)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            update_call_status(conn, call_id, "error", "Ollama no ha retornat JSON vàlid")
            print("ERROR: Ollama no ha retornat JSON vàlid.")
            print(f"Resposta crua guardada a: {raw_file}")
            print("Resposta netejada:")
            print(cleaned[:2000])
            sys.exit(1)

        json_file.write_text(
            json.dumps(parsed, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        elapsed = round(time.time() - started, 2)

        print("[3/3] Guardant anàlisi a PostgreSQL...")
        save_analysis(
            conn=conn,
            call_id=call_id,
            service_type=service_type,
            call_date=call_date,
            parsed=parsed,
            processing_seconds=elapsed,
        )

        with (LOGS_DIR / "analyze_call.log").open("a", encoding="utf-8") as log:
            log.write(
                f"OK call_id={call_id} "
                f"file={original_filename} "
                f"seconds={elapsed} "
                f"model={OLLAMA_MODEL}\n"
            )

        print("==========================================")
        print("Fet.")
        print(f"RAW:  {raw_file}")
        print(f"JSON: {json_file}")
        print(f"Temps anàlisi: {elapsed} segons")
        print("Estat BBDD: analyzed")
        print("==========================================")
        print(json.dumps(parsed, ensure_ascii=False, indent=2))

    except requests.exceptions.ConnectionError:
        msg = f"No puc connectar amb Ollama a {OLLAMA_URL}"
        update_call_status(conn, call_id, "error", msg)
        print("ERROR:")
        print(msg)
        print()
        print("Comprova des de Debian:")
        print(f"  curl {OLLAMA_URL}/api/tags")
        sys.exit(1)

    except requests.exceptions.HTTPError as e:
        msg = f"Error HTTP amb Ollama: {e}"
        update_call_status(conn, call_id, "error", msg)
        print("ERROR:")
        print(msg)
        if e.response is not None:
            print(e.response.text)
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
