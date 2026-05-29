#!/bin/bash
set -euo pipefail

MONTH="${1:-}"
INCLUDE_SENSITIVE="${2:-no}"

if [ -z "$MONTH" ]; then
  echo "Ús:"
  echo "  $0 YYYY-MM [yes|no]"
  echo
  echo "Exemples:"
  echo "  $0 2026-05"
  echo "  $0 2026-05 yes"
  exit 1
fi

cd /srv/call-ai
source .venv/bin/activate

if [ "$INCLUDE_SENSITIVE" = "yes" ]; then
  echo "[1/2] Generant informe mensual AMB identificadors..."
  /srv/call-ai/scripts/export_monthly_report.py \
    --month "$MONTH" \
    --include-identifiers

  echo "[2/2] Creant ZIP SENSIBLE..."
  /srv/call-ai/scripts/zip_monthly_report.py \
    --month "$MONTH" \
    --include-sensitive
else
  echo "[1/2] Generant informe mensual sense identificadors..."
  /srv/call-ai/scripts/export_monthly_report.py \
    --month "$MONTH"

  echo "[2/2] Creant ZIP normal..."
  /srv/call-ai/scripts/zip_monthly_report.py \
    --month "$MONTH"
fi

echo
echo "Fitxers disponibles a:"
echo "  /srv/call-ai/reports/exports/"
ls -lh /srv/call-ai/reports/exports/
