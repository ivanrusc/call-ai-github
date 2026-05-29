# Backups Call-AI

## Objectiu

El sistema tracta àudios, transcripcions i dades potencialment personals.

Cal fer còpies de seguretat de:

```text
PostgreSQL
scripts
.env
àudios originals
transcripcions
anàlisis
informes
````

## Què NO cal copiar sempre

Els fitxers WAV temporals no cal copiar-los:

```text
/srv/call-ai/tmp_wav/
```

Són temporals i es poden regenerar a partir dels àudios originals.

## Estratègia recomanada

### Diari

```text
- Backup PostgreSQL
- Backup scripts
- Backup .env xifrat
- Backup nous àudios
- Backup transcripcions i anàlisis
```

### Setmanal

```text
- Backup complet de /srv/call-ai
- Verificació de restauració
```

### Mensual

```text
- Export mensual ZIP
- Backup complet xifrat
- Conservació segons política del client
```

## Backup PostgreSQL manual

```bash
cd /srv/call-ai
set -a
source .env
set +a

mkdir -p /srv/call-ai/backups/postgres

TS="$(date +'%F_%H-%M-%S')"

PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  -Fc \
  -f "/srv/call-ai/backups/postgres/${TS}_call_ai.dump"
```

## Restaurar PostgreSQL

Atenció: restaurar pot sobreescriure dades.

```bash
cd /srv/call-ai
set -a
source .env
set +a

PGPASSWORD="$POSTGRES_PASSWORD" pg_restore \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --clean \
  --if-exists \
  "/srv/call-ai/backups/postgres/FITXER.dump"
```

## Backup de fitxers

Exemple:

```bash
TS="$(date +'%F_%H-%M-%S')"

tar -czf "/srv/call-ai/backups/${TS}_call-ai-files.tar.gz" \
  --exclude="/srv/call-ai/tmp_wav" \
  --exclude="/srv/call-ai/db/postgres" \
  --exclude="/srv/call-ai/.venv" \
  /srv/call-ai
```

## Backup complet recomanat

Incloure:

```text
/srv/call-ai/audio_in
/srv/call-ai/audio_archive
/srv/call-ai/transcripts
/srv/call-ai/analysis
/srv/call-ai/reports
/srv/call-ai/scripts
/srv/call-ai/db/init
/srv/call-ai/.env
```

No incloure:

```text
/srv/call-ai/tmp_wav
/srv/call-ai/.venv
/srv/call-ai/db/postgres
```

La BBDD es copia amb `pg_dump`, no copiant directament `db/postgres`.

## Script suggerit de backup

Crear:

```bash
nano /srv/call-ai/scripts/backup_call_ai.sh
```

Contingut:

```bash
#!/bin/bash
set -euo pipefail

BASE_DIR="/srv/call-ai"
BACKUP_DIR="$BASE_DIR/backups"
TS="$(date +'%F_%H-%M-%S')"

cd "$BASE_DIR"

set -a
source "$BASE_DIR/.env"
set +a

mkdir -p "$BACKUP_DIR/postgres"
mkdir -p "$BACKUP_DIR/files"

echo "[1/3] Backup PostgreSQL..."

PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  -Fc \
  -f "$BACKUP_DIR/postgres/${TS}_call_ai.dump"

echo "[2/3] Backup fitxers..."

tar -czf "$BACKUP_DIR/files/${TS}_call-ai-files.tar.gz" \
  --exclude="$BASE_DIR/tmp_wav" \
  --exclude="$BASE_DIR/db/postgres" \
  --exclude="$BASE_DIR/.venv" \
  --exclude="$BASE_DIR/backups" \
  "$BASE_DIR"

echo "[3/3] Checksums..."

sha256sum "$BACKUP_DIR/postgres/${TS}_call_ai.dump" \
  > "$BACKUP_DIR/postgres/${TS}_call_ai.dump.sha256"

sha256sum "$BACKUP_DIR/files/${TS}_call-ai-files.tar.gz" \
  > "$BACKUP_DIR/files/${TS}_call-ai-files.tar.gz.sha256"

echo "Backup complet:"
echo "  $BACKUP_DIR/postgres/${TS}_call_ai.dump"
echo "  $BACKUP_DIR/files/${TS}_call-ai-files.tar.gz"
```

Permisos:

```bash
chmod +x /srv/call-ai/scripts/backup_call_ai.sh
```

Executar:

```bash
/srv/call-ai/scripts/backup_call_ai.sh
```

## Automatitzar backup amb cron

Editar:

```bash
crontab -e
```

Afegir:

```cron
30 2 * * * /srv/call-ai/scripts/backup_call_ai.sh >> /srv/call-ai/logs/backup.log 2>&1
```

Això executa el backup cada dia a les 02:30.

## Retenció recomanada

Exemple:

```text
Diari: conservar 14 dies
Setmanal: conservar 8 setmanes
Mensual: conservar 12 mesos
```

## Esborrar backups antics

Exemple per esborrar backups diaris de més de 30 dies:

```bash
find /srv/call-ai/backups/postgres -type f -mtime +30 -delete
find /srv/call-ai/backups/files -type f -mtime +30 -delete
```

## Còpia externa

Si el client té un servidor extern:

```bash
rsync -avz /srv/call-ai/backups/ usuari@servidor:/ruta/backups/call-ai/
```

Amb SSH key recomanat.

## Xifrat

Si els backups surten del servidor del client, s'han de xifrar.

Opcions:

```text
gpg
age
restic
borgbackup
```

Recomanació pràctica:

```text
restic + repositori xifrat
```

## Verificació

Una còpia no és fiable fins que s'ha provat una restauració.

Com a mínim mensualment:

```text
1. Crear una BBDD de prova
2. Restaurar dump
3. Comprovar taules
4. Comprovar nombre de trucades
5. Comprovar transcripcions
```

SQL de comprovació:

```sql
SELECT COUNT(*) FROM calls;
SELECT COUNT(*) FROM transcripts;
SELECT COUNT(*) FROM call_motives;
SELECT COUNT(*) FROM call_identifiers;
``` 
