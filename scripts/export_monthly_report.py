#!/usr/bin/env python3
import os
import csv
import sys
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


load_dotenv("/srv/call-ai/.env")

BASE_DIR = Path(os.getenv("CALL_AI_BASE", "/srv/call-ai"))
REPORTS_DIR = BASE_DIR / "reports"

DB = {
    "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB", "call_ai"),
    "user": os.getenv("POSTGRES_USER", "call_ai"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}


def db_connect():
    return psycopg2.connect(**DB)


def parse_month(month_str: str):
    try:
        start = datetime.strptime(month_str, "%Y-%m").date()
    except ValueError:
        print("ERROR: El format de --month ha de ser YYYY-MM. Exemple: 2026-05")
        sys.exit(1)

    if start.month == 12:
        end = date(start.year + 1, 1, 1)
    else:
        end = date(start.year, start.month + 1, 1)

    return start, end


def ensure_report_dir(month_str: str):
    out_dir = REPORTS_DIR / month_str
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def fetch_all(conn, query, params=None):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params or {})
        return cur.fetchall()


def write_csv(path: Path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter=";",
            extrasaction="ignore"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def md_table(rows, columns, max_rows=15):
    if not rows:
        return "_Sense dades._\n"

    rows = rows[:max_rows]

    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"

    lines = [header, sep]

    for row in rows:
        values = []
        for col in columns:
            value = row.get(col, "")
            if value is None:
                value = ""
            values.append(str(value).replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines) + "\n"


def get_summary_counts(conn, start, end):
    return fetch_all(
        conn,
        """
        SELECT
            service_type,
            status,
            COUNT(*) AS total
        FROM calls
        WHERE call_date >= %(start)s
          AND call_date < %(end)s
        GROUP BY service_type, status
        ORDER BY service_type, status;
        """,
        {"start": start, "end": end},
    )


def export_reports(conn, out_dir: Path, start, end, include_identifiers=False):
    params = {"start": start, "end": end}

    # 01 - Trucades
    calls = fetch_all(
        conn,
        """
        SELECT
            c.id,
            c.call_date,
            c.service_type,
            c.original_filename,
            c.duration_seconds,
            c.status,
            c.created_at,
            c.updated_at,
            a.resum_general,
            a.idioma
        FROM calls c
        LEFT JOIN call_analysis a ON a.call_id = c.id
        WHERE c.call_date >= %(start)s
          AND c.call_date < %(end)s
        ORDER BY c.call_date, c.id;
        """,
        params,
    )
    write_csv(out_dir / "01_trucades.csv", calls)

    # 02 - Motius repetits
    motius_repetits = fetch_all(
        conn,
        """
        SELECT
            service_type,
            motiu_agrupat,
            resolucio,
            es_emergencia,
            COUNT(*) AS vegades,
            COUNT(*) FILTER (WHERE es_reserva = true) AS consultes_reserva,
            COUNT(*) FILTER (WHERE reserva_finalitzada = false) AS reserves_no_finalitzades,
            COUNT(*) FILTER (WHERE es_fallada_punt_carrega = true) AS fallades_punt_carrega
        FROM call_motives
        WHERE call_date >= %(start)s
          AND call_date < %(end)s
        GROUP BY
            service_type,
            motiu_agrupat,
            resolucio,
            es_emergencia
        ORDER BY service_type, vegades DESC, motiu_agrupat;
        """,
        params,
    )
    write_csv(out_dir / "02_motius_repetits.csv", motius_repetits)

    # 03 - Motius detall
    motius_detall = fetch_all(
        conn,
        """
        SELECT
            c.id AS call_id,
            c.call_date,
            c.service_type,
            c.original_filename,
            m.consulta_num,
            m.motiu_original,
            m.motiu_agrupat,
            m.resolucio,
            m.es_emergencia,
            m.es_reserva,
            m.reserva_finalitzada,
            m.motiu_reserva_no_finalitzada,
            m.es_fallada_punt_carrega,
            m.accio_recomanada,
            m.confianca_classificacio
        FROM call_motives m
        JOIN calls c ON c.id = m.call_id
        WHERE m.call_date >= %(start)s
          AND m.call_date < %(end)s
        ORDER BY c.call_date, c.id, m.consulta_num;
        """,
        params,
    )
    write_csv(out_dir / "03_motius_detall.csv", motius_detall)

    # 04 - Trucades per dia
    trucades_per_dia = fetch_all(
        conn,
        """
        SELECT
            call_date,
            COUNT(*) FILTER (WHERE service_type = 'assistencia') AS assistencia,
            COUNT(*) FILTER (WHERE service_type = 'oficina') AS oficina,
            COUNT(*) AS total
        FROM calls
        WHERE call_date >= %(start)s
          AND call_date < %(end)s
        GROUP BY call_date
        ORDER BY call_date;
        """,
        params,
    )
    write_csv(out_dir / "04_trucades_per_dia.csv", trucades_per_dia)

    # 05 - Paraules clau
    keywords = fetch_all(
        conn,
        """
        SELECT
            service_type,
            keyword_normalized,
            COUNT(*) AS vegades
        FROM call_keywords
        WHERE call_date >= %(start)s
          AND call_date < %(end)s
        GROUP BY service_type, keyword_normalized
        ORDER BY service_type, vegades DESC, keyword_normalized;
        """,
        params,
    )
    write_csv(out_dir / "05_paraules_clau.csv", keywords)

    # 06 - Resum assistència
    resum_assistencia = fetch_all(
        conn,
        """
        SELECT
            motiu_agrupat,
            COUNT(*) AS vegades,
            COUNT(*) FILTER (WHERE es_emergencia = true) AS emergències,
            COUNT(*) FILTER (WHERE es_reserva = true) AS consultes_reserva,
            COUNT(*) FILTER (WHERE reserva_finalitzada = false) AS reserves_no_finalitzades,
            COUNT(*) FILTER (WHERE es_fallada_punt_carrega = true) AS fallades_punt_carrega
        FROM call_motives
        WHERE service_type = 'assistencia'
          AND call_date >= %(start)s
          AND call_date < %(end)s
        GROUP BY motiu_agrupat
        ORDER BY vegades DESC, motiu_agrupat;
        """,
        params,
    )
    write_csv(out_dir / "06_resum_assistencia.csv", resum_assistencia)

    # 07 - Resum oficina
    resum_oficina = fetch_all(
        conn,
        """
        SELECT
            motiu_agrupat,
            COUNT(*) AS vegades,
            COUNT(*) FILTER (WHERE es_emergencia = true) AS emergències,
            COUNT(*) FILTER (WHERE es_reserva = true) AS consultes_reserva,
            COUNT(*) FILTER (WHERE reserva_finalitzada = false) AS reserves_no_finalitzades,
            COUNT(*) FILTER (WHERE es_fallada_punt_carrega = true) AS fallades_punt_carrega
        FROM call_motives
        WHERE service_type = 'oficina'
          AND call_date >= %(start)s
          AND call_date < %(end)s
        GROUP BY motiu_agrupat
        ORDER BY vegades DESC, motiu_agrupat;
        """,
        params,
    )
    write_csv(out_dir / "07_resum_oficina.csv", resum_oficina)

    # 08 - Reserves no finalitzades
    reserves_no_finalitzades = fetch_all(
        conn,
        """
        SELECT
            service_type,
            motiu_reserva_no_finalitzada,
            COUNT(*) AS vegades,
            COUNT(*) FILTER (WHERE es_fallada_punt_carrega = true) AS fallades_punt_carrega
        FROM call_motives
        WHERE es_reserva = true
          AND reserva_finalitzada = false
          AND call_date >= %(start)s
          AND call_date < %(end)s
        GROUP BY service_type, motiu_reserva_no_finalitzada
        ORDER BY vegades DESC;
        """,
        params,
    )
    write_csv(out_dir / "08_reserves_no_finalitzades.csv", reserves_no_finalitzades)

    # 09 - Identificadors SENSIBLE
    identificadors = []
    if include_identifiers:
        identificadors = fetch_all(
            conn,
            """
            SELECT
                c.id AS call_id,
                c.call_date,
                c.service_type,
                c.original_filename,
                i.identifier_type,
                i.identifier_value,
                i.confidence,
                i.context_fragment
            FROM call_identifiers i
            JOIN calls c ON c.id = i.call_id
            WHERE i.call_date >= %(start)s
              AND i.call_date < %(end)s
            ORDER BY c.call_date, c.id, i.identifier_type;
            """,
            params,
        )
        write_csv(out_dir / "09_identificadors_detectats_SENSIBLE.csv", identificadors)

    return {
        "calls": calls,
        "motius_repetits": motius_repetits,
        "motius_detall": motius_detall,
        "trucades_per_dia": trucades_per_dia,
        "keywords": keywords,
        "resum_assistencia": resum_assistencia,
        "resum_oficina": resum_oficina,
        "reserves_no_finalitzades": reserves_no_finalitzades,
        "identificadors": identificadors,
    }


def write_markdown_summary(out_dir: Path, month_str, start, end, data, include_identifiers=False):
    calls = data["calls"]
    resum_assistencia = data["resum_assistencia"]
    resum_oficina = data["resum_oficina"]
    trucades_per_dia = data["trucades_per_dia"]
    reserves_no_finalitzades = data["reserves_no_finalitzades"]
    keywords = data["keywords"]

    total_calls = len(calls)
    total_assistencia = sum(1 for r in calls if r.get("service_type") == "assistencia")
    total_oficina = sum(1 for r in calls if r.get("service_type") == "oficina")

    total_consultes = len(data["motius_detall"])
    total_emergencies = sum(1 for r in data["motius_detall"] if r.get("es_emergencia") is True)
    total_reserves_no_finalitzades = sum(
        1 for r in data["motius_detall"]
        if r.get("es_reserva") is True and r.get("reserva_finalitzada") is False
    )
    total_fallades_carrega = sum(
        1 for r in data["motius_detall"]
        if r.get("es_fallada_punt_carrega") is True
    )

    md = []
    md.append(f"# Informe resum de trucades — {month_str}\n")
    md.append(f"Període: **{start}** fins **{end - timedelta(days=1)}**\n")
    md.append("\n")

    md.append("## Resum general\n")
    md.append(f"- Total trucades: **{total_calls}**\n")
    md.append(f"- Trucades assistència: **{total_assistencia}**\n")
    md.append(f"- Trucades oficina: **{total_oficina}**\n")
    md.append(f"- Total consultes/motius detectats: **{total_consultes}**\n")
    md.append(f"- Emergències detectades: **{total_emergencies}**\n")
    md.append(f"- Reserves no finalitzades: **{total_reserves_no_finalitzades}**\n")
    md.append(f"- Fallades de punt de càrrega: **{total_fallades_carrega}**\n")
    md.append("\n")

    md.append("## Motius més habituals — Assistència\n")
    md.append(md_table(
        resum_assistencia,
        [
            "motiu_agrupat",
            "vegades",
            "emergències",
            "consultes_reserva",
            "reserves_no_finalitzades",
            "fallades_punt_carrega",
        ],
        max_rows=15,
    ))
    md.append("\n")

    md.append("## Motius més habituals — Oficina\n")
    md.append(md_table(
        resum_oficina,
        [
            "motiu_agrupat",
            "vegades",
            "emergències",
            "consultes_reserva",
            "reserves_no_finalitzades",
            "fallades_punt_carrega",
        ],
        max_rows=15,
    ))
    md.append("\n")

    md.append("## Trucades per dia\n")
    md.append(md_table(
        trucades_per_dia,
        [
            "call_date",
            "assistencia",
            "oficina",
            "total",
        ],
        max_rows=40,
    ))
    md.append("\n")

    md.append("## Reserves no finalitzades\n")
    md.append(md_table(
        reserves_no_finalitzades,
        [
            "service_type",
            "motiu_reserva_no_finalitzada",
            "vegades",
            "fallades_punt_carrega",
        ],
        max_rows=20,
    ))
    md.append("\n")

    md.append("## Paraules clau més habituals\n")
    md.append(md_table(
        keywords,
        [
            "service_type",
            "keyword_normalized",
            "vegades",
        ],
        max_rows=30,
    ))
    md.append("\n")

    md.append("## Fitxers generats\n")
    md.append("- `01_trucades.csv`\n")
    md.append("- `02_motius_repetits.csv`\n")
    md.append("- `03_motius_detall.csv`\n")
    md.append("- `04_trucades_per_dia.csv`\n")
    md.append("- `05_paraules_clau.csv`\n")
    md.append("- `06_resum_assistencia.csv`\n")
    md.append("- `07_resum_oficina.csv`\n")
    md.append("- `08_reserves_no_finalitzades.csv`\n")

    if include_identifiers:
        md.append("- `09_identificadors_detectats_SENSIBLE.csv`\n")
        md.append("\n")
        md.append("> ATENCIÓ: el fitxer d'identificadors conté dades personals o potencialment identificatives.\n")
    else:
        md.append("\n")
        md.append("> No s'ha exportat el fitxer d'identificadors personals. Per generar-lo cal executar amb `--include-identifiers`.\n")

    report_file = out_dir / "informe_resum.md"
    report_file.write_text("".join(md), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Exporta CSVs i informe mensual de trucades."
    )

    parser.add_argument(
        "--month",
        required=True,
        help="Mes a exportar en format YYYY-MM. Exemple: 2026-05",
    )

    parser.add_argument(
        "--include-identifiers",
        action="store_true",
        help="Exporta també dades identificatives. Fitxer sensible.",
    )

    args = parser.parse_args()

    start, end = parse_month(args.month)
    out_dir = ensure_report_dir(args.month)

    conn = db_connect()

    try:
        print("==========================================")
        print("EXPORT MENSUAL CALL-AI")
        print("==========================================")
        print(f"Mes:                  {args.month}")
        print(f"Període:              {start} -> {end - timedelta(days=1)}")
        print(f"Directori sortida:    {out_dir}")
        print(f"Include identifiers:  {args.include_identifiers}")
        print("==========================================")

        data = export_reports(
            conn=conn,
            out_dir=out_dir,
            start=start,
            end=end,
            include_identifiers=args.include_identifiers,
        )

        write_markdown_summary(
            out_dir=out_dir,
            month_str=args.month,
            start=start,
            end=end,
            data=data,
            include_identifiers=args.include_identifiers,
        )

        print()
        print("Fitxers generats:")
        for path in sorted(out_dir.iterdir()):
            print(f" - {path}")

        print()
        print("Fet.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
