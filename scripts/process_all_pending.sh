#!/bin/bash
set -euo pipefail

BASE_DIR="/srv/call-ai"
LOG_FILE="$BASE_DIR/logs/process_all_pending.log"
LOCK_FILE="/tmp/call-ai-process.lock"
BATCH_SIZE="${BATCH_SIZE:-10}"

cd "$BASE_DIR"

mkdir -p "$BASE_DIR/logs"

# Evita que s'executin dues còpies alhora
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "$(date '+%F %T') - Ja hi ha un procés Call-AI en execució. Surto." | tee -a "$LOG_FILE"
  exit 0
fi

echo "==========================================" | tee -a "$LOG_FILE"
echo "$(date '+%F %T') - Inici process_all_pending" | tee -a "$LOG_FILE"
echo "BATCH_SIZE=$BATCH_SIZE" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"

# Carregar .env
set -a
source "$BASE_DIR/.env"
set +a

# Activar entorn Python
source "$BASE_DIR/.venv/bin/activate"

# Registrar fitxers nous al lot actiu.
# De moment fem servir batch_id=1.
echo "$(date '+%F %T') - Registrant fitxers nous a la BBDD..." | tee -a "$LOG_FILE"
"$BASE_DIR/scripts/register_audio_files.py" 1 2>&1 | tee -a "$LOG_FILE"

get_pending_count() {
  PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -Atc "
      SELECT COUNT(*)
      FROM calls
      WHERE status IN ('imported', 'transcribed');
    "
}

PENDING="$(get_pending_count)"

echo "$(date '+%F %T') - Pendents inicials: $PENDING" | tee -a "$LOG_FILE"

if [ "$PENDING" -eq 0 ]; then
  echo "$(date '+%F %T') - No hi ha trucades pendents." | tee -a "$LOG_FILE"
  exit 0
fi

ROUND=1

while [ "$PENDING" -gt 0 ]; do
  echo "------------------------------------------" | tee -a "$LOG_FILE"
  echo "$(date '+%F %T') - Ronda $ROUND - pendents: $PENDING" | tee -a "$LOG_FILE"
  echo "------------------------------------------" | tee -a "$LOG_FILE"

  "$BASE_DIR/scripts/process_pending_calls.py" \
    --limit "$BATCH_SIZE" \
    2>&1 | tee -a "$LOG_FILE"

  PENDING="$(get_pending_count)"
  ROUND=$((ROUND + 1))
done

echo "==========================================" | tee -a "$LOG_FILE"
echo "$(date '+%F %T') - Final process_all_pending. Pendents: $PENDING" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"
