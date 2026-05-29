# Resolució d'errors — Call-AI

## 1. Començar el diagnòstic

Comandes bàsiques:

```bash
docker ps
sudo systemctl status call-ai-process-all.timer --no-pager
sudo systemctl status call-ai-process-all.service --no-pager
tail -n 100 /srv/call-ai/logs/process_all_pending.log
````

Veure estat de trucades:

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

```sql
SELECT status, COUNT(*)
FROM calls
GROUP BY status
ORDER BY status;
```

Veure errors:

```sql
SELECT id, original_filename, call_date, service_type, error_message
FROM calls
WHERE status = 'error'
ORDER BY updated_at DESC
LIMIT 20;
```

Sortir:

```sql
\q
```

## 2. Error: PostgreSQL no respon

### Símptomes

```text
connection refused
could not connect to server
psql: error
```

### Comprovar Docker

```bash
docker ps
```

Si no apareix `call-ai-postgres`:

```bash
cd /srv/call-ai
docker compose up -d
```

Veure logs:

```bash
docker logs call-ai-postgres --tail=100
```

### Reiniciar PostgreSQL

```bash
cd /srv/call-ai
docker compose restart postgres
```

### Comprovar port

```bash
ss -lntp | grep 5432
```

Ha de sortir escoltant a:

```text
127.0.0.1:5432
```

## 3. Error: `.env` no existeix

### Símptomes

```text
No such file or directory: /srv/call-ai/.env
```

### Solució

Crear a partir de l'exemple:

```bash
cp /srv/call-ai-github/.env.example /srv/call-ai/.env
nano /srv/call-ai/.env
```

Revisar contrasenya, IP Ollama i models.

## 4. Error: `.venv` no existeix

### Símptomes

```text
-bash: .venv/bin/activate: No such file or directory
```

### Solució

```bash
cd /srv/call-ai

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install psycopg2-binary python-dotenv requests faster-whisper
```

## 5. Error: `ModuleNotFoundError: No module named psycopg2`

### Solució

```bash
cd /srv/call-ai
source .venv/bin/activate

pip install psycopg2-binary
```

Validar:

```bash
python -c "import psycopg2; print('OK')"
```

## 6. Error: `ModuleNotFoundError: No module named faster_whisper`

### Solució

```bash
cd /srv/call-ai
source .venv/bin/activate

pip install faster-whisper
```

Validar:

```bash
python -c "from faster_whisper import WhisperModel; print('OK')"
```

## 7. Error: `ModuleNotFoundError: No module named requests`

### Solució

```bash
cd /srv/call-ai
source .venv/bin/activate

pip install requests
```

## 8. Error: script no trobat

### Símptoma

```text
transcribe_call.py: command not found
```

### Causa

Linux no busca automàticament dins `/srv/call-ai/scripts`.

### Solució

Executar amb ruta completa:

```bash
/srv/call-ai/scripts/transcribe_call.py 1
```

O amb Python:

```bash
python /srv/call-ai/scripts/transcribe_call.py 1
```

## 9. Error: permisos d'script

### Símptoma

```text
Permission denied
```

### Solució

```bash
chmod +x /srv/call-ai/scripts/*.py
chmod +x /srv/call-ai/scripts/*.sh
```

## 10. Error: `SyntaxError` o `IndentationError`

### Símptoma

```text
SyntaxError: unmatched ')'
IndentationError: unexpected indent
```

### Causa

S'ha editat un script i ha quedat mal indentat.

### Diagnòstic

```bash
cd /srv/call-ai
source .venv/bin/activate

python -m py_compile /srv/call-ai/scripts/NOM_SCRIPT.py
```

### Solució

Restaurar des de GitHub o backup:

```bash
cp /srv/call-ai-github/scripts/NOM_SCRIPT.py /srv/call-ai/scripts/
chmod +x /srv/call-ai/scripts/NOM_SCRIPT.py
```

Validar:

```bash
python -m py_compile /srv/call-ai/scripts/NOM_SCRIPT.py
```

## 11. Error: ffmpeg no instal·lat

### Símptoma

```text
No such file or directory: ffmpeg
Error convertint àudio amb ffmpeg
```

### Solució

```bash
sudo apt update
sudo apt install -y ffmpeg
```

Comprovar:

```bash
ffmpeg -version
```

## 12. Error: àudio no existeix

### Símptoma

```text
No existeix el fitxer: /srv/call-ai/audio_in/...
```

### Diagnòstic

```bash
ls -lh /srv/call-ai/audio_in/
find /srv/call-ai/audio_in -type f
```

Consultar ruta a BBDD:

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

```sql
SELECT id, original_filename, original_path, status
FROM calls
WHERE id = 1;
```

### Solució

Restaurar el fitxer o eliminar la trucada de BBDD si no ha d'existir.

## 13. Error: no es registren àudios

### Diagnòstic

```bash
find /srv/call-ai/audio_in -type f
```

Comprovar extensions suportades:

```text
.mp3
.wav
.m4a
.aac
.ogg
.flac
.wma
```

Executar registre:

```bash
cd /srv/call-ai
source .venv/bin/activate

/srv/call-ai/scripts/register_audio_files.py 1
```

Si diu `Fitxers trobats: 0`, revisar que els fitxers estiguin dins:

```text
/srv/call-ai/audio_in/
```

## 14. Error: data no detectada

### Causa

La subcarpeta no té format correcte.

Correcte:

```text
/srv/call-ai/audio_in/2026-05-29/trucada.mp3
```

Incorrecte:

```text
/srv/call-ai/audio_in/29-05-2026/trucada.mp3
/srv/call-ai/audio_in/maig/trucada.mp3
```

Format requerit:

```text
YYYY-MM-DD
```

Després de corregir carpetes:

```bash
/srv/call-ai/scripts/register_audio_files.py 1
```

## 15. Error: assistència/oficina mal classificat

### Regla

```text
Si el nom conté ASSISTENCIA_VALUE → assistencia
Si no → oficina
```

Veure configuració:

```bash
grep ASSISTENCIA_VALUE /srv/call-ai/.env
```

Canviar:

```bash
nano /srv/call-ai/.env
```

Reprocessar registre:

```bash
/srv/call-ai/scripts/register_audio_files.py 1
```

Consultar:

```sql
SELECT id, original_filename, service_type
FROM calls
ORDER BY id DESC
LIMIT 20;
```

## 16. Error: Ollama no respon

### Símptoma

```text
No puc connectar amb Ollama
Connection refused
```

### Diagnòstic des de Debian

```bash
cd /srv/call-ai
set -a
source .env
set +a

curl "$OLLAMA_URL/api/tags"
```

### Comprovar Mac

Al Mac mini:

```bash
ollama list
```

Provar local:

```bash
curl http://127.0.0.1:11434/api/tags
```

### Si només funciona al Mac però no des de Debian

Ollama probablement no escolta a la LAN.

Al Mac:

```bash
launchctl setenv OLLAMA_HOST "0.0.0.0:11434"
osascript -e 'quit app "Ollama"'
```

Obrir Ollama de nou.

Comprovar:

```bash
lsof -nP -iTCP:11434 -sTCP:LISTEN
```

Des de Debian:

```bash
curl http://IP_MAC:11434/api/tags
```

## 17. Error: model Ollama no existeix

### Símptoma

```text
model not found
```

### Solució al Mac

```bash
ollama pull qwen3:8b
ollama list
```

Revisar `.env` a Debian:

```bash
grep OLLAMA_MODEL /srv/call-ai/.env
```

## 18. Error: Ollama retorna JSON no vàlid

### Símptoma

```text
Ollama no ha retornat JSON vàlid
```

### Revisar fitxer raw

```bash
ls -lh /srv/call-ai/analysis/
cat /srv/call-ai/analysis/*raw.txt
```

### Solució

Reexecutar:

```bash
/srv/call-ai/scripts/analyze_call.py ID_TRUCADA
```

Si passa sovint:

```text
- baixar temperatura al prompt
- simplificar prompt
- usar un model millor
- revisar transcripció
```

## 19. Error: transcripció dolenta

### Símptomes

```text
idioma mal detectat
text inventat
paraules estranyes
massa errors
```

### Revisar configuració

```bash
grep WHISPER /srv/call-ai/.env
```

Opció recomanada:

```bash
WHISPER_MODEL=medium
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_LANGUAGE=es
WHISPER_VAD=false
```

Provar català:

```bash
sed -i 's/^WHISPER_LANGUAGE=.*/WHISPER_LANGUAGE=ca/' /srv/call-ai/.env
/srv/call-ai/scripts/transcribe_call.py ID_TRUCADA
```

Provar auto:

```bash
sed -i 's/^WHISPER_LANGUAGE=.*/WHISPER_LANGUAGE=auto/' /srv/call-ai/.env
/srv/call-ai/scripts/transcribe_call.py ID_TRUCADA
```

Provar model small o medium:

```bash
sed -i 's/^WHISPER_MODEL=.*/WHISPER_MODEL=medium/' /srv/call-ai/.env
```

## 20. Error: procés molt lent

### Possibles causes

```text
WHISPER_MODEL=medium en CPU
moltes trucades pendents
Mac/Ollama lent
BATCH_SIZE massa alt
```

### Diagnòstic

```bash
tail -f /srv/call-ai/logs/process_all_pending.log
```

### Solucions

Reduir batch:

```bash
sudo nano /etc/systemd/system/call-ai-process-all.service
```

Canviar:

```ini
Environment=BATCH_SIZE=5
```

Aplicar:

```bash
sudo systemctl daemon-reload
```

Usar Whisper `small`:

```bash
sed -i 's/^WHISPER_MODEL=.*/WHISPER_MODEL=small/' /srv/call-ai/.env
```

## 21. Error: timer no s'executa

### Diagnòstic

```bash
systemctl list-timers | grep call-ai
sudo systemctl status call-ai-process-all.timer --no-pager
```

### Activar

```bash
sudo systemctl enable --now call-ai-process-all.timer
```

### Veure logs

```bash
journalctl -u call-ai-process-all.service -n 200 --no-pager
```

## 22. Error: ja hi ha un procés en execució

### Missatge

```text
Ja hi ha un procés Call-AI en execució. Surto.
```

### Explicació

El sistema evita dues execucions simultànies amb `flock`.

### Comprovar procés

```bash
ps aux | grep call-ai
```

Si realment està penjat, revisar abans de matar.

## 23. Error: disc ple

### Diagnòstic

```bash
df -h
du -sh /srv/call-ai/*
```

### Netejar temporals

```bash
find /srv/call-ai/tmp_wav -type f -delete
```

### Revisar backups

```bash
du -sh /srv/call-ai/backups/*
```

### Revisar àudios

```bash
du -sh /srv/call-ai/audio_in
du -sh /srv/call-ai/audio_archive
```

## 24. Error: no es genera informe mensual

### Comprovar que hi ha dades del mes

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

```sql
SELECT call_date, COUNT(*)
FROM calls
WHERE call_date >= '2026-05-01'
  AND call_date < '2026-06-01'
GROUP BY call_date
ORDER BY call_date;
```

### Generar informe

```bash
/srv/call-ai/scripts/export_monthly_report.py --month 2026-05
```

### Generar paquet

```bash
/srv/call-ai/scripts/make_monthly_package.sh 2026-05
```

## 25. Error: CSV buit

Causes habituals:

```text
- no hi ha trucades en aquell mes
- call_date és NULL
- no s'han analitzat trucades
- s'ha demanat el mes equivocat
```

Comprovar:

```sql
SELECT id, original_filename, call_date, status
FROM calls
ORDER BY id DESC
LIMIT 20;
```

## 26. Error: identificadors falsos

Exemple:

```text
30 euros detectat com numero_reserva
```

L'script `analyze_call.py` ja té filtre.

Si encara passa:

```text
1. Afegir regla a should_keep_identifier()
2. Reanalitzar la trucada
```

Reanalitzar:

```bash
/srv/call-ai/scripts/analyze_call.py ID_TRUCADA
```

## 27. Posar una trucada en estat concret

Entrar a PostgreSQL:

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

Marcar com importada:

```sql
UPDATE calls
SET status = 'imported',
    error_message = NULL,
    updated_at = now()
WHERE id = 1;
```

Marcar com transcrita:

```sql
UPDATE calls
SET status = 'transcribed',
    error_message = NULL,
    updated_at = now()
WHERE id = 1;
```

Marcar per revisió:

```sql
UPDATE calls
SET status = 'needs_review',
    updated_at = now()
WHERE id = 1;
```

## 28. Reprocessar una trucada des de zero

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

```sql
DELETE FROM call_identifiers WHERE call_id = 1;
DELETE FROM call_keywords WHERE call_id = 1;
DELETE FROM call_motives WHERE call_id = 1;
DELETE FROM call_analysis WHERE call_id = 1;
DELETE FROM transcripts WHERE call_id = 1;

UPDATE calls
SET status = 'imported',
    error_message = NULL,
    updated_at = now()
WHERE id = 1;
```

Després:

```bash
/srv/call-ai/scripts/process_pending_calls.py --limit 1
```

## 29. Recuperar scripts des del repositori

```bash
cp /srv/call-ai-github/scripts/* /srv/call-ai/scripts/
chmod +x /srv/call-ai/scripts/*
```

Validar sintaxi:

```bash
cd /srv/call-ai
source .venv/bin/activate

python -m py_compile /srv/call-ai/scripts/*.py
```

## 30. Checklist ràpid

Quan alguna cosa falla:

```text
1. docker ps
2. systemctl list-timers | grep call-ai
3. tail -n 100 /srv/call-ai/logs/process_all_pending.log
4. /srv/call-ai/scripts/psql-call-ai.sh
5. SELECT status, COUNT(*) FROM calls GROUP BY status;
6. curl "$OLLAMA_URL/api/tags"
7. df -h
8. python -m py_compile scripts/*.py
```
