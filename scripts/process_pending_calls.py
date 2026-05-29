#!/usr/bin/env python3
import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


load_dotenv("/srv/call-ai/.env")

BASE_DIR = Path(os.getenv("CALL_AI_BASE", "/srv/call-ai"))
SCRIPTS_DIR = BASE_DIR / "scripts"
LOGS_DIR = BASE_DIR / "logs"

TRANSCRIBE_SCRIPT = SCRIPTS_DIR / "transcribe_call.py"
ANALYZE_SCRIPT = SCRIPTS_DIR / "analyze_call.py"

DB = {
    "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB", "call_ai"),
    "user": os.getenv("POSTGRES_USER", "call_ai"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

LOGS_DIR.mkdir(parents=True, exist_ok=True)


def db_connect():
    return psycopg2.connect(**DB)


def get_pending_calls(conn, limit: int, retry_errors: bool = False):
    statuses = ["imported", "transcribed"]

    if retry_errors:
        statuses.append("error")

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                id,
                original_filename,
                service_type,
                call_date,
                status
            FROM calls
            WHERE status = ANY(%s)
            ORDER BY
                call_date NULLS LAST,
                id
            LIMIT %s
            """,
            (statuses, limit),
        )
        return cur.fetchall()


def get_call_status(conn, call_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT status
            FROM calls
            WHERE id = %s
            """,
            (call_id,),
        )
        row = cur.fetchone()

    if not row:
        return None

    return row[0]


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


def run_script(script_path: Path, call_id: int):
    if not script_path.exists():
        raise FileNotFoundError(f"No existeix: {script_path}")

    cmd = [
        sys.executable,
        str(script_path),
        str(call_id),
    ]

    started = time.time()

    result = subprocess.run(
        cmd,
        cwd=str(BASE_DIR),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    elapsed = round(time.time() - started, 2)

    return result.returncode, result.stdout, elapsed


def append_log(text: str):
    log_file = LOGS_DIR / "process_pending_calls.log"

    with log_file.open("a", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def print_status_summary(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT status, COUNT(*)
            FROM calls
            GROUP BY status
            ORDER BY status
            """
        )
        rows = cur.fetchall()

    print()
    print("==========================================")
    print("RESUM STATUS")
    print("==========================================")

    if not rows:
        print("No hi ha trucades registrades.")
        return

    for status, count in rows:
        print(f"{status:15} {count}")


def main():
    parser = argparse.ArgumentParser(
        description="Processa trucades pendents: transcripció + anàlisi."
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Nombre màxim de trucades a processar. Per defecte: 5",
    )

    parser.add_argument(
        "--retry-errors",
        action="store_true",
        help="Inclou trucades amb status='error'.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra què processaria però no executa res.",
    )

    parser.add_argument(
        "--skip-transcribe",
        action="store_true",
        help="No transcriu. Només analitza trucades ja transcrites.",
    )

    parser.add_argument(
        "--skip-analyze",
        action="store_true",
        help="No analitza. Només transcriu trucades importades.",
    )

    args = parser.parse_args()

    if args.limit <= 0:
        print("ERROR: --limit ha de ser superior a 0")
        sys.exit(1)

    conn = db_connect()

    try:
        pending = get_pending_calls(
            conn=conn,
            limit=args.limit,
            retry_errors=args.retry_errors,
        )

        print("==========================================")
        print("PROCESSADOR DE TRUCADES PENDENTS")
        print("==========================================")
        print(f"Limit:          {args.limit}")
        print(f"Retry errors:   {args.retry_errors}")
        print(f"Dry run:        {args.dry_run}")
        print(f"Skip transcribe:{args.skip_transcribe}")
        print(f"Skip analyze:   {args.skip_analyze}")
        print(f"Pendents:       {len(pending)}")
        print("==========================================")

        if not pending:
            print("No hi ha trucades pendents.")
            print_status_summary(conn)
            return

        for row in pending:
            call_id, filename, service_type, call_date, status = row

            print()
            print("------------------------------------------")
            print(f"CALL_ID:      {call_id}")
            print(f"Fitxer:       {filename}")
            print(f"Servei:       {service_type}")
            print(f"Data:         {call_date}")
            print(f"Status:       {status}")
            print("------------------------------------------")

            append_log(
                f"START call_id={call_id} file={filename} status={status}"
            )

            if args.dry_run:
                print("DRY RUN: no faig res.")
                continue

            try:
                current_status = get_call_status(conn, call_id)

                if current_status is None:
                    print(f"ERROR: call_id={call_id} ja no existeix.")
                    continue

                # Si ve d'error i fem retry, tornem a imported
                if current_status == "error" and args.retry_errors:
                    print("Reintentant trucada amb error. Status → imported")
                    update_call_status(conn, call_id, "imported", None)
                    current_status = "imported"

                # Transcripció
                if current_status == "imported":
                    if args.skip_transcribe:
                        print("Skip transcribe activat. No transcric.")
                    else:
                        print("[1/2] Transcrivint...")
                        code, output, elapsed = run_script(TRANSCRIBE_SCRIPT, call_id)

                        print(output)

                        append_log(
                            f"TRANSCRIBE call_id={call_id} code={code} seconds={elapsed}"
                        )

                        if code != 0:
                            print(f"ERROR transcrivint call_id={call_id}")
                            append_log(
                                f"ERROR_TRANSCRIBE call_id={call_id} output={output[-1000:]}"
                            )
                            continue

                current_status = get_call_status(conn, call_id)

                # Anàlisi
                if current_status == "transcribed":
                    if args.skip_analyze:
                        print("Skip analyze activat. No analitzo.")
                    else:
                        print("[2/2] Analitzant amb Ollama...")
                        code, output, elapsed = run_script(ANALYZE_SCRIPT, call_id)

                        print(output)

                        append_log(
                            f"ANALYZE call_id={call_id} code={code} seconds={elapsed}"
                        )

                        if code != 0:
                            print(f"ERROR analitzant call_id={call_id}")
                            append_log(
                                f"ERROR_ANALYZE call_id={call_id} output={output[-1000:]}"
                            )
                            continue

                final_status = get_call_status(conn, call_id)

                print(f"FINAL STATUS: {final_status}")
                append_log(f"DONE call_id={call_id} final_status={final_status}")

            except KeyboardInterrupt:
                print()
                print("Procés interromput manualment.")
                append_log("INTERRUPTED_BY_USER")
                sys.exit(130)

            except Exception as e:
                msg = str(e)
                print(f"ERROR inesperat call_id={call_id}: {msg}")
                update_call_status(conn, call_id, "error", msg)
                append_log(f"ERROR_UNEXPECTED call_id={call_id} msg={msg}")
                continue

        print_status_summary(conn)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
