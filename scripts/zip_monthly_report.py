#!/usr/bin/env python3
import argparse
import hashlib
import os
import sys
import zipfile
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv


load_dotenv("/srv/call-ai/.env")

BASE_DIR = Path(os.getenv("CALL_AI_BASE", "/srv/call-ai"))
REPORTS_DIR = BASE_DIR / "reports"
EXPORTS_DIR = REPORTS_DIR / "exports"

SENSITIVE_PATTERNS = [
    "SENSIBLE",
    "identificadors",
    "identificadores",
    "dni",
    "telefon",
    "telèfon",
    "email",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def is_sensitive(path: Path) -> bool:
    name = path.name.lower()

    for pattern in SENSITIVE_PATTERNS:
        if pattern.lower() in name:
            return True

    return False


def collect_files(report_dir: Path, include_sensitive: bool):
    files = []

    for path in sorted(report_dir.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix == ".zip":
            continue

        if not include_sensitive and is_sensitive(path):
            continue

        files.append(path)

    return files


def write_manifest(report_dir: Path, files, include_sensitive: bool):
    manifest = []

    manifest.append("# Manifest export mensual Call-AI\n")
    manifest.append(f"Generat: {datetime.now().isoformat(timespec='seconds')}\n")
    manifest.append(f"Directori origen: {report_dir}\n")
    manifest.append(f"Inclou fitxers sensibles: {include_sensitive}\n")
    manifest.append("\n")
    manifest.append("## Fitxers inclosos\n\n")

    for path in files:
        rel = path.relative_to(report_dir)
        size = path.stat().st_size
        digest = sha256_file(path)

        manifest.append(f"- `{rel}` — {size} bytes — sha256 `{digest}`\n")

    manifest_path = report_dir / "MANIFEST_EXPORT.md"
    manifest_path.write_text("".join(manifest), encoding="utf-8")

    return manifest_path


def main():
    parser = argparse.ArgumentParser(
        description="Crea un ZIP mensual amb els informes i CSVs de Call-AI."
    )

    parser.add_argument(
        "--month",
        required=True,
        help="Mes en format YYYY-MM. Exemple: 2026-05",
    )

    parser.add_argument(
        "--include-sensitive",
        action="store_true",
        help="Inclou fitxers sensibles com identificadors personals.",
    )

    args = parser.parse_args()

    report_dir = REPORTS_DIR / args.month

    if not report_dir.exists():
        print(f"ERROR: No existeix el directori d'informe: {report_dir}")
        print()
        print("Primer genera l'informe mensual:")
        print(f"  /srv/call-ai/scripts/export_monthly_report.py --month {args.month}")
        sys.exit(1)

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    files = collect_files(
        report_dir=report_dir,
        include_sensitive=args.include_sensitive,
    )

    if not files:
        print(f"ERROR: No hi ha fitxers per empaquetar a {report_dir}")
        sys.exit(1)

    manifest_path = write_manifest(
        report_dir=report_dir,
        files=files,
        include_sensitive=args.include_sensitive,
    )

    files.append(manifest_path)

    suffix = "-SENSIBLE" if args.include_sensitive else ""
    zip_name = f"call-ai-{args.month}{suffix}.zip"
    zip_path = EXPORTS_DIR / zip_name

    if zip_path.exists():
        zip_path.unlink()

    print("==========================================")
    print("ZIP MENSUAL CALL-AI")
    print("==========================================")
    print(f"Mes:                 {args.month}")
    print(f"Directori informe:   {report_dir}")
    print(f"Include sensitive:   {args.include_sensitive}")
    print(f"ZIP sortida:         {zip_path}")
    print(f"Fitxers:             {len(files)}")
    print("==========================================")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            arcname = Path(args.month) / path.relative_to(report_dir)
            zf.write(path, arcname)

    digest = sha256_file(zip_path)

    sha_file = zip_path.with_suffix(zip_path.suffix + ".sha256")
    sha_file.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")

    print()
    print("Fet.")
    print(f"ZIP:    {zip_path}")
    print(f"SHA256: {sha_file}")
    print()
    print(f"Mida ZIP: {round(zip_path.stat().st_size / 1024 / 1024, 2)} MB")


if __name__ == "__main__":
    main()
