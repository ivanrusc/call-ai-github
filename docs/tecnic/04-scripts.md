# Scripts Call-AI

Aquest document descriu els scripts principals del sistema.

## Carpeta

Els scripts de producció estan a:

```text
/srv/call-ai/scripts/
````

Al repositori GitHub estan a:

```text
scripts/
```

## Llista de scripts

```text
psql-call-ai.sh
register_audio_files.py
transcribe_call.py
analyze_call.py
process_pending_calls.py
process_all_pending.sh
export_monthly_report.py
zip_monthly_report.py
make_monthly_package.sh
```

---

## `psql-call-ai.sh`

Obre una sessió PostgreSQL carregant les variables del `.env`.

Ús:

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

Sortir:

```sql
\q
```

---

## `register_audio_files.py`

Registra àudios dins la BBDD.

Busca fitxers a:

```text
/srv/call-ai/audio_in/
```

Extensions suportades:

```text
.mp3
.wav
.m4a
.aac
.ogg
.flac
.wma
```

Ús:

```bash
/srv/call-ai/scripts/register_audio_files.py BATCH_ID
```

Exemple:

```bash
/srv/call-ai/scripts/register_audio_files.py 1
```

Què fa:

```text
1. Busca àudios dins audio_in/
2. Detecta data per subcarpeta YYYY-MM-DD
3. Detecta assistència/oficina segons nom del fitxer
4. Registra la trucada a calls
5. Evita duplicats per original_path
```

Regla assistència:

```text
Si el nom conté 34930185139 → assistencia
Si no → oficina
```

---

## `transcribe_call.py`

Transcriu una trucada concreta.

Ús:

```bash
/srv/call-ai/scripts/transcribe_call.py CALL_ID
```

Exemple:

```bash
/srv/call-ai/scripts/transcribe_call.py 1
```

Què fa:

```text
1. Llegeix la trucada de PostgreSQL
2. Converteix l'àudio a WAV temporal
3. Transcriu amb faster-whisper
4. Genera TXT
5. Genera SRT
6. Genera JSON de segments
7. Guarda transcripció a PostgreSQL
8. Esborra WAV temporal
9. Canvia status a transcribed
```

Variables `.env`:

```bash
WHISPER_MODEL=medium
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_LANGUAGE=es
WHISPER_VAD=false
```

Models recomanats:

```text
small   més ràpid, menys qualitat
medium  més lent, millor qualitat
```

---

## `analyze_call.py`

Analitza una trucada ja transcrita amb Ollama.

Ús:

```bash
/srv/call-ai/scripts/analyze_call.py CALL_ID
```

Exemple:

```bash
/srv/call-ai/scripts/analyze_call.py 1
```

Què fa:

```text
1. Llegeix la transcripció de PostgreSQL
2. Envia el text a Ollama
3. Rep JSON d'anàlisi
4. Valida JSON
5. Guarda call_analysis
6. Guarda call_motives
7. Guarda call_keywords
8. Guarda call_identifiers
9. Actualitza transcripció anonimitzada
10. Canvia status a analyzed
```

Variables `.env`:

```bash
OLLAMA_URL=http://192.168.1.9:11434
OLLAMA_MODEL=qwen3:8b
```

Filtre d'identificadors:

L'script evita guardar falsos identificadors com:

```text
30 euros
5 a 8 de la tarda
imports
hores
durades
```

---

## `process_pending_calls.py`

Processa trucades pendents amb control de límit.

Ús normal:

```bash
/srv/call-ai/scripts/process_pending_calls.py --limit 5
```

Opcions:

```bash
--limit N
--dry-run
--skip-transcribe
--skip-analyze
--retry-errors
```

Exemples:

### Veure què processaria

```bash
/srv/call-ai/scripts/process_pending_calls.py --limit 5 --dry-run
```

### Processar 5 trucades

```bash
/srv/call-ai/scripts/process_pending_calls.py --limit 5
```

### Només transcriure

```bash
/srv/call-ai/scripts/process_pending_calls.py --limit 5 --skip-analyze
```

### Només analitzar

```bash
/srv/call-ai/scripts/process_pending_calls.py --limit 5 --skip-transcribe
```

### Reintentar errors

```bash
/srv/call-ai/scripts/process_pending_calls.py --limit 5 --retry-errors
```

---

## `process_all_pending.sh`

Processa totes les trucades pendents.

Ús:

```bash
/srv/call-ai/scripts/process_all_pending.sh
```

Què fa:

```text
1. Registra fitxers nous
2. Compta pendents
3. Processa per rondes
4. Continua fins que no queda cap imported/transcribed
5. Escriu log
6. Evita dues execucions simultànies amb flock
```

Variable:

```bash
BATCH_SIZE=10
```

No és un límit total.
Si hi ha 1.200 trucades, les processa en rondes de 10 fins acabar.

Log:

```bash
/srv/call-ai/logs/process_all_pending.log
```

---

## `export_monthly_report.py`

Genera CSVs i informe mensual Markdown.

Ús:

```bash
/srv/call-ai/scripts/export_monthly_report.py --month 2026-05
```

Amb identificadors personals:

```bash
/srv/call-ai/scripts/export_monthly_report.py \
  --month 2026-05 \
  --include-identifiers
```

Fitxers generats:

```text
01_trucades.csv
02_motius_repetits.csv
03_motius_detall.csv
04_trucades_per_dia.csv
05_paraules_clau.csv
06_resum_assistencia.csv
07_resum_oficina.csv
08_reserves_no_finalitzades.csv
09_identificadors_detectats_SENSIBLE.csv
informe_resum.md
```

El fitxer `09_identificadors_detectats_SENSIBLE.csv` només es genera amb `--include-identifiers`.

---

## `zip_monthly_report.py`

Crea un ZIP mensual.

Ús:

```bash
/srv/call-ai/scripts/zip_monthly_report.py --month 2026-05
```

Amb fitxers sensibles:

```bash
/srv/call-ai/scripts/zip_monthly_report.py \
  --month 2026-05 \
  --include-sensitive
```

Sortida:

```text
/srv/call-ai/reports/exports/call-ai-2026-05.zip
/srv/call-ai/reports/exports/call-ai-2026-05.zip.sha256
```

Amb dades sensibles:

```text
/srv/call-ai/reports/exports/call-ai-2026-05-SENSIBLE.zip
```

---

## `make_monthly_package.sh`

Helper per generar informe + ZIP.

Ús normal:

```bash
/srv/call-ai/scripts/make_monthly_package.sh 2026-05
```

Amb dades sensibles:

```bash
/srv/call-ai/scripts/make_monthly_package.sh 2026-05 yes
```

---

## Logs importants

```text
/srv/call-ai/logs/process_all_pending.log
/srv/call-ai/logs/transcribe_call.log
/srv/call-ai/logs/analyze_call.log
```

Veure en directe:

```bash
tail -f /srv/call-ai/logs/process_all_pending.log
```

---

## Ordre normal del procés

Manual:

```bash
/srv/call-ai/scripts/register_audio_files.py 1
/srv/call-ai/scripts/process_all_pending.sh
/srv/call-ai/scripts/make_monthly_package.sh 2026-05
```

Automàtic:

```text
systemd timer → process_all_pending.sh
```
