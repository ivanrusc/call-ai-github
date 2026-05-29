# Manual de comandes Call-AI

## Entrar al servidor

```bash
ssh usuari@IP_SERVIDOR
```
Anar al projecte

```bash
cd /srv/call-ai
source .venv/bin/activate
```

Veure estat de PostgreSQL
```bash
docker ps
```

Entrar a la BBDD
```bash
/srv/call-ai/scripts/psql-call-ai.sh
```
Sortir:
```SQL
\q
```
Veure estat de trucades
```SQL
SELECT status, COUNT(*)
FROM calls
GROUP BY status
ORDER BY status;
```
Registrar àudios nous
```bash
/srv/call-ai/scripts/register_audio_files.py 1
```
Processar totes les trucades pendents
```bash
/srv/call-ai/scripts/process_all_pending.sh
```
Processar un nombre limitat de trucades
```bash
/srv/call-ai/scripts/process_pending_calls.py --limit 5
```
Nomes transcriure
```bash
/srv/call-ai/scripts/process_pending_calls.py --limit 5 --skip-analyze
```
Nomes analitzar trucades ja transcrites
```bash
/srv/call-ai/scripts/process_pending_calls.py --limit 5 --skip-transcribe
```
Generar informe mensual
```bash
/srv/call-ai/scripts/export_monthly_report.py --month 2026-05
```
Generar ZIP mensual
```bash
/srv/call-ai/scripts/zip_monthly_report.py --month 2026-05
```
Generar paquet mensual complet
```bash
/srv/call-ai/scripts/make_monthly_package.sh 2026-05
```
Generar paquet amb dades sensibles
```bash
/srv/call-ai/scripts/make_monthly_package.sh 2026-05 yes
```
Veure logs
```bash
tail -f /srv/call-ai/logs/process_all_pending.log
```
Veure timer automàtic
```bash
systemctl list-timers | grep call-ai
```
Llan(s)ar procés automàtic manualment
```bash
sudo systemctl start call-ai-process-all.service
```
Veure estat del servei
```bash
sudo systemctl status call-ai-process-all.service --no-pager
```
