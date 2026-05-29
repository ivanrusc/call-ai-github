# Manual de manteniment — Call-AI

## 1. Objectiu

Aquest document recull les tasques habituals de manteniment del sistema Call-AI.

El sistema està format per:

```text
Debian:
  - PostgreSQL
  - scripts Python
  - àudios
  - transcripcions
  - informes
  - automatització systemd

Mac mini M4:
  - Ollama
  - model qwen3:8b
````

## 2. Carpetes principals

```text
/srv/call-ai/
├── audio_in/
├── audio_archive/
├── tmp_wav/
├── transcripts/
├── analysis/
├── reports/
├── scripts/
├── db/
├── logs/
└── backups/
```

## 3. Comprovar estat general

### Docker

```bash
docker ps
```

Ha d'aparèixer:

```text
call-ai-postgres
```

### PostgreSQL

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

Dins PostgreSQL:

```sql
SELECT status, COUNT(*)
FROM calls
GROUP BY status
ORDER BY status;
```

Sortir:

```sql
\q
```

### Timer automàtic

```bash
systemctl list-timers | grep call-ai
```

### Servei automàtic

```bash
sudo systemctl status call-ai-process-all.service --no-pager
```

### Logs

```bash
tail -n 100 /srv/call-ai/logs/process_all_pending.log
```

En directe:

```bash
tail -f /srv/call-ai/logs/process_all_pending.log
```

## 4. Flux normal diari

El sistema hauria de funcionar així:

```text
1. Entren àudios nous a /srv/call-ai/audio_in/YYYY-MM-DD/
2. El timer executa el procés automàtic.
3. Es registren fitxers nous.
4. Es transcriuen.
5. S'analitzen amb Ollama.
6. Es guarden resultats a PostgreSQL.
```

## 5. Llançar procés manual

Si cal executar el procés manualment:

```bash
sudo systemctl start call-ai-process-all.service
```

O directament:

```bash
cd /srv/call-ai
source .venv/bin/activate

/srv/call-ai/scripts/process_all_pending.sh
```

## 6. Registrar àudios manualment

Si s'han copiat fitxers nous i es vol registrar manualment:

```bash
cd /srv/call-ai
source .venv/bin/activate

/srv/call-ai/scripts/register_audio_files.py 1
```

El `1` és el `batch_id`.

Per veure lots:

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

```sql
SELECT id, name, batch_type, period_start, period_end
FROM import_batches
ORDER BY id DESC;
```

## 7. Processar només unes quantes trucades

Per provar sense processar-ho tot:

```bash
cd /srv/call-ai
source .venv/bin/activate

/srv/call-ai/scripts/process_pending_calls.py --limit 5
```

Veure què faria sense executar:

```bash
/srv/call-ai/scripts/process_pending_calls.py --limit 5 --dry-run
```

## 8. Només transcriure

```bash
/srv/call-ai/scripts/process_pending_calls.py --limit 5 --skip-analyze
```

Això deixa les trucades en estat:

```text
transcribed
```

## 9. Només analitzar

```bash
/srv/call-ai/scripts/process_pending_calls.py --limit 5 --skip-transcribe
```

Això agafa trucades ja transcrites i les passa a:

```text
analyzed
```

## 10. Reintentar errors

Si hi ha trucades en error:

```bash
/srv/call-ai/scripts/process_pending_calls.py --limit 5 --retry-errors
```

Veure errors:

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

```sql
SELECT id, original_filename, service_type, call_date, status, error_message
FROM calls
WHERE status = 'error'
ORDER BY updated_at DESC
LIMIT 20;
```

## 11. Transcriure una trucada concreta

```bash
cd /srv/call-ai
source .venv/bin/activate

/srv/call-ai/scripts/transcribe_call.py ID_TRUCADA
```

Exemple:

```bash
/srv/call-ai/scripts/transcribe_call.py 1
```

## 12. Analitzar una trucada concreta

```bash
cd /srv/call-ai
source .venv/bin/activate

/srv/call-ai/scripts/analyze_call.py ID_TRUCADA
```

Exemple:

```bash
/srv/call-ai/scripts/analyze_call.py 1
```

## 13. Consultar transcripció d'una trucada

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

```sql
SELECT
    c.id,
    c.original_filename,
    t.language,
    t.whisper_model,
    left(t.transcript_text, 1000) AS inici_transcripcio
FROM calls c
JOIN transcripts t ON t.call_id = c.id
WHERE c.id = 1;
```

## 14. Consultar motius detectats

```sql
SELECT
    c.id,
    c.original_filename,
    c.service_type,
    c.call_date,
    m.consulta_num,
    m.motiu_agrupat,
    m.resolucio,
    m.es_emergencia,
    m.es_reserva,
    m.reserva_finalitzada,
    m.es_fallada_punt_carrega
FROM calls c
JOIN call_motives m ON m.call_id = c.id
WHERE c.id = 1
ORDER BY m.consulta_num;
```

## 15. Consultar identificadors detectats

```sql
SELECT
    identifier_type,
    identifier_value,
    confidence,
    context_fragment
FROM call_identifiers
WHERE call_id = 1
ORDER BY identifier_type;
```

Aquest resultat pot contenir dades personals.

## 16. Consultar paraules clau

```sql
SELECT
    keyword_normalized,
    COUNT(*) AS vegades
FROM call_keywords
WHERE call_id = 1
GROUP BY keyword_normalized
ORDER BY keyword_normalized;
```

## 17. Generar informe mensual

```bash
cd /srv/call-ai
source .venv/bin/activate

/srv/call-ai/scripts/export_monthly_report.py --month 2026-05
```

## 18. Generar ZIP mensual

```bash
/srv/call-ai/scripts/zip_monthly_report.py --month 2026-05
```

## 19. Generar paquet mensual complet

Sense dades personals:

```bash
/srv/call-ai/scripts/make_monthly_package.sh 2026-05
```

Amb dades personals:

```bash
/srv/call-ai/scripts/make_monthly_package.sh 2026-05 yes
```

## 20. Ubicació dels informes

```text
/srv/call-ai/reports/YYYY-MM/
```

Exemple:

```bash
ls -lh /srv/call-ai/reports/2026-05/
```

ZIPs:

```bash
ls -lh /srv/call-ai/reports/exports/
```

## 21. Revisar espai de disc

```bash
df -h
```

Espai del projecte:

```bash
du -sh /srv/call-ai/*
```

Carpetes que més poden créixer:

```text
audio_in/
audio_archive/
transcripts/
analysis/
reports/
backups/
```

## 22. Netejar WAV temporals

Els WAV temporals no s'han de conservar.

```bash
find /srv/call-ai/tmp_wav -type f -delete
```

## 23. Reiniciar PostgreSQL

```bash
cd /srv/call-ai
docker compose restart postgres
```

Veure logs:

```bash
docker logs call-ai-postgres --tail=100
```

## 24. Reiniciar timer

```bash
sudo systemctl restart call-ai-process-all.timer
```

## 25. Parar automatització

```bash
sudo systemctl stop call-ai-process-all.timer
```

## 26. Activar automatització

```bash
sudo systemctl enable --now call-ai-process-all.timer
```

## 27. Desactivar automatització

```bash
sudo systemctl disable --now call-ai-process-all.timer
```

## 28. Veure logs systemd

```bash
journalctl -u call-ai-process-all.service -n 200 --no-pager
```

En directe:

```bash
journalctl -u call-ai-process-all.service -f
```

## 29. Backup manual

```bash
/srv/call-ai/scripts/backup_call_ai.sh
```

Si aquest script no existeix, veure document:

```text
docs/tecnic/05-backups.md
```

## 30. Actualitzar codi des de GitHub

Si el projecte està connectat a Git:

```bash
cd /srv/call-ai-github
git pull
```

Després copiar scripts actualitzats a producció:

```bash
cp scripts/* /srv/call-ai/scripts/
chmod +x /srv/call-ai/scripts/*
```

Si s'han canviat SQLs, revisar manualment abans d'aplicar.

## 31. Recomanació mensual

Cada mes:

```text
1. Comprovar que no hi ha errors.
2. Generar informe mensual.
3. Generar ZIP mensual.
4. Fer backup.
5. Revisar espai de disc.
6. Revisar motius més habituals.
```

Comandes:

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

```sql
SELECT status, COUNT(*)
FROM calls
GROUP BY status
ORDER BY status;
```

```bash
/srv/call-ai/scripts/make_monthly_package.sh YYYY-MM
/srv/call-ai/scripts/backup_call_ai.sh
df -h
du -sh /srv/call-ai/*
```
