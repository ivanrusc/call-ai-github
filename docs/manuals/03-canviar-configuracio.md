# Canviar configuració — Call-AI

## 1. Fitxer principal de configuració

La configuració principal és:

```text
/srv/call-ai/.env
````

Editar:

```bash
nano /srv/call-ai/.env
```

Després de canviar valors, normalment cal tornar a executar el procés o reiniciar el servei/timer segons el canvi.

## 2. Veure configuració actual

```bash
cat /srv/call-ai/.env
```

Veure només configuració Whisper:

```bash
grep WHISPER /srv/call-ai/.env
```

Veure configuració Ollama:

```bash
grep OLLAMA /srv/call-ai/.env
```

Veure configuració PostgreSQL:

```bash
grep POSTGRES /srv/call-ai/.env
```

## 3. Canviar IP d'Ollama

Variable:

```bash
OLLAMA_URL=http://192.168.1.9:11434
```

Canviar:

```bash
nano /srv/call-ai/.env
```

Exemple:

```bash
OLLAMA_URL=http://192.168.1.72:11434
```

Provar:

```bash
cd /srv/call-ai
set -a
source .env
set +a

curl "$OLLAMA_URL/api/tags"
```

## 4. Canviar model d'Ollama

Variable:

```bash
OLLAMA_MODEL=qwen3:8b
```

Canviar a un altre model disponible:

```bash
OLLAMA_MODEL=gemma3:12b
```

Comprovar models al Mac:

```bash
curl "$OLLAMA_URL/api/tags"
```

Després provar una anàlisi:

```bash
cd /srv/call-ai
source .venv/bin/activate

/srv/call-ai/scripts/analyze_call.py 1
```

## 5. Canviar model Whisper

Variables:

```bash
WHISPER_MODEL=medium
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_LANGUAGE=es
WHISPER_VAD=false
```

### Opció ràpida

Més ràpid, menys qualitat:

```bash
WHISPER_MODEL=small
```

### Opció recomanada

Més qualitat, més lent:

```bash
WHISPER_MODEL=medium
```

### Canviar amb `sed`

```bash
sed -i 's/^WHISPER_MODEL=.*/WHISPER_MODEL=medium/' /srv/call-ai/.env
```

O:

```bash
sed -i 's/^WHISPER_MODEL=.*/WHISPER_MODEL=small/' /srv/call-ai/.env
```

## 6. Canviar idioma Whisper

Variable:

```bash
WHISPER_LANGUAGE=es
```

Opcions habituals:

```text
es    castellà
ca    català
auto  detecció automàtica
```

Canviar a català:

```bash
sed -i 's/^WHISPER_LANGUAGE=.*/WHISPER_LANGUAGE=ca/' /srv/call-ai/.env
```

Canviar a castellà:

```bash
sed -i 's/^WHISPER_LANGUAGE=.*/WHISPER_LANGUAGE=es/' /srv/call-ai/.env
```

Canviar a automàtic:

```bash
sed -i 's/^WHISPER_LANGUAGE=.*/WHISPER_LANGUAGE=auto/' /srv/call-ai/.env
```

## 7. Activar o desactivar VAD

VAD és el filtre de detecció de veu.

Variable:

```bash
WHISPER_VAD=false
```

### Desactivat

Recomanat si el VAD talla fragments importants:

```bash
WHISPER_VAD=false
```

### Activat

Pot anar bé si hi ha silencis llargs:

```bash
WHISPER_VAD=true
```

Canviar:

```bash
sed -i 's/^WHISPER_VAD=.*/WHISPER_VAD=false/' /srv/call-ai/.env
```

o:

```bash
sed -i 's/^WHISPER_VAD=.*/WHISPER_VAD=true/' /srv/call-ai/.env
```

## 8. Canviar regla assistència / oficina

Variable:

```bash
ASSISTENCIA_VALUE=34930185139
```

Regla:

```text
Si el nom del fitxer conté aquest valor → assistencia
Si no → oficina
```

Canviar:

```bash
nano /srv/call-ai/.env
```

Exemple:

```bash
ASSISTENCIA_VALUE=34930185139
```

Després, si ja hi havia trucades registrades, cal tornar a registrar fitxers perquè actualitzi `service_type`:

```bash
cd /srv/call-ai
source .venv/bin/activate

/srv/call-ai/scripts/register_audio_files.py 1
```

## 9. Canviar mida de lot de processament

El servei systemd fa servir:

```ini
Environment=BATCH_SIZE=10
```

Fitxer:

```text
/etc/systemd/system/call-ai-process-all.service
```

Editar:

```bash
sudo nano /etc/systemd/system/call-ai-process-all.service
```

Canviar, per exemple:

```ini
Environment=BATCH_SIZE=5
```

o:

```ini
Environment=BATCH_SIZE=20
```

Aplicar:

```bash
sudo systemctl daemon-reload
sudo systemctl restart call-ai-process-all.timer
```

Nota:

`BATCH_SIZE` no limita el total. Només processa per rondes.

## 10. Canviar freqüència del timer

Fitxer:

```text
/etc/systemd/system/call-ai-process-all.timer
```

Editar:

```bash
sudo nano /etc/systemd/system/call-ai-process-all.timer
```

### Cada hora

```ini
[Timer]
OnBootSec=10min
OnUnitActiveSec=1h
Persistent=true
Unit=call-ai-process-all.service
```

### Cada 30 minuts

```ini
[Timer]
OnBootSec=10min
OnUnitActiveSec=30min
Persistent=true
Unit=call-ai-process-all.service
```

### Cada nit a les 23:30

```ini
[Timer]
OnCalendar=*-*-* 23:30:00
Persistent=true
Unit=call-ai-process-all.service
```

Aplicar:

```bash
sudo systemctl daemon-reload
sudo systemctl restart call-ai-process-all.timer
```

Comprovar:

```bash
systemctl list-timers | grep call-ai
```

## 11. Canviar usuari del servei systemd

Fitxer:

```bash
sudo nano /etc/systemd/system/call-ai-process-all.service
```

Línia:

```ini
User=sommob
```

Canviar per l'usuari correcte.

Aplicar:

```bash
sudo systemctl daemon-reload
sudo systemctl restart call-ai-process-all.timer
```

## 12. Canviar ubicació del projecte

Per defecte:

```bash
CALL_AI_BASE=/srv/call-ai
```

Si es canvia, cal revisar:

```text
.env
scripts
systemd service
compose.yaml
rutes de BBDD
```

No és recomanable canviar-ho després d'haver posat el sistema en producció.

## 13. Canviar contrasenya PostgreSQL

Aquest canvi requereix més cura.

Entrar a PostgreSQL:

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

Canviar password:

```sql
ALTER USER call_ai WITH PASSWORD 'nova_contrasenya_segura';
```

Sortir:

```sql
\q
```

Editar `.env`:

```bash
nano /srv/call-ai/.env
```

Canviar:

```bash
POSTGRES_PASSWORD=nova_contrasenya_segura
```

Reiniciar contenidor:

```bash
cd /srv/call-ai
docker compose restart postgres
```

Provar:

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

## 14. Canviar port PostgreSQL

Per defecte només escolta a localhost:

```yaml
ports:
  - "127.0.0.1:5432:5432"
```

No es recomana exposar PostgreSQL a la LAN.

Si cal canviar port local:

```yaml
ports:
  - "127.0.0.1:5433:5432"
```

També cal canviar `.env`:

```bash
POSTGRES_PORT=5433
```

Aplicar:

```bash
cd /srv/call-ai
docker compose down
docker compose up -d
```

## 15. Canviar prompt d'anàlisi

El prompt està dins:

```text
/srv/call-ai/scripts/analyze_call.py
```

Funció:

```python
build_prompt(...)
```

Editar:

```bash
nano /srv/call-ai/scripts/analyze_call.py
```

Validar sintaxi:

```bash
cd /srv/call-ai
source .venv/bin/activate

python -m py_compile /srv/call-ai/scripts/analyze_call.py
```

Provar amb una trucada:

```bash
/srv/call-ai/scripts/analyze_call.py 1
```

## 16. Canviar motius agrupats recomanats

Dins `analyze_call.py`, buscar:

```text
Motius agrupats recomanats:
```

Afegir o modificar categories.

Després reanalitzar trucades si cal:

```bash
/srv/call-ai/scripts/analyze_call.py ID_TRUCADA
```

## 17. Reprocessar després de canvis de configuració

### Si canvies Whisper

Cal tornar a transcriure:

```bash
/srv/call-ai/scripts/transcribe_call.py ID_TRUCADA
/srv/call-ai/scripts/analyze_call.py ID_TRUCADA
```

### Si canvies prompt o model Ollama

Només cal reanalitzar:

```bash
/srv/call-ai/scripts/analyze_call.py ID_TRUCADA
```

### Reprocessar moltes trucades

Posar status manualment:

```sql
UPDATE calls
SET status = 'transcribed'
WHERE call_date >= '2026-05-01'
  AND call_date < '2026-06-01';
```

Després:

```bash
/srv/call-ai/scripts/process_all_pending.sh
```

## 18. Canviar permisos de fitxers

Projecte:

```bash
sudo chown -R sommob:sommob /srv/call-ai
chmod 750 /srv/call-ai
chmod 600 /srv/call-ai/.env
chmod +x /srv/call-ai/scripts/*
```

## 19. Afegir un nou lot

Entrar a PostgreSQL:

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

Crear lot:

```sql
INSERT INTO import_batches
(name, batch_type, period_start, period_end, source_folder, notes)
VALUES
('Import juny 2026', 'mensual', '2026-06-01', '2026-06-30', '/srv/call-ai/audio_in', 'Import mensual')
RETURNING id, name;
```

Sortir:

```sql
\q
```

Registrar fitxers amb el nou ID:

```bash
/srv/call-ai/scripts/register_audio_files.py ID_DEL_LOT
```

## 20. Recomanació

Abans de canvis importants:

```text
1. Fer backup.
2. Canviar configuració.
3. Validar sintaxi.
4. Provar amb 1 trucada.
5. Provar amb 5 trucades.
6. Activar processament normal.
```
