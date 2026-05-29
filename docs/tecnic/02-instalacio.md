##
# Instal·lació tècnica Call-AI

## Objectiu

Aquest document descriu la instal·lació tècnica del sistema Call-AI en una Debian neta.

El sistema està pensat per funcionar 100% en local dins la infraestructura del client.

## Arquitectura

```text
Debian VM / CT
  ├── PostgreSQL en Docker
  ├── scripts Python
  ├── faster-whisper per STT
  ├── àudios originals
  ├── transcripcions
  ├── anàlisis
  ├── informes
  └── backups

Mac mini M4
  └── Ollama + qwen3:8b
````

## Requisits recomanats

### Debian

Recomanat per producció:

```text
Debian 13
6 vCPU
12 GB RAM
250 GB disc mínim
Docker
Python 3
```

Mínim funcional:

```text
4 vCPU
8 GB RAM
150 GB disc
```

### Mac mini M4

```text
Mac mini M4
16 GB RAM
Ollama instal·lat
Model qwen3:8b descarregat
```

## Instal·lació base Debian

```bash
sudo apt update
sudo apt upgrade -y

sudo apt install -y \
  curl \
  wget \
  git \
  nano \
  jq \
  htop \
  tree \
  unzip \
  ca-certificates \
  gnupg \
  lsb-release \
  ffmpeg \
  python3 \
  python3-venv \
  python3-pip \
  build-essential \
  libpq-dev \
  postgresql-client
```

## Instal·lació Docker

Eliminar paquets conflictius:

```bash
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do
  sudo apt remove -y "$pkg" 2>/dev/null || true
done
```

Afegir clau i repositori Docker:

```bash
sudo install -m 0755 -d /etc/apt/keyrings

sudo curl -fsSL https://download.docker.com/linux/debian/gpg \
  -o /etc/apt/keyrings/docker.asc

sudo chmod a+r /etc/apt/keyrings/docker.asc
```

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Instal·lar Docker:

```bash
sudo apt update

sudo apt install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

Activar Docker:

```bash
sudo systemctl enable --now docker
```

Afegir usuari al grup Docker:

```bash
sudo usermod -aG docker "$USER"
```

Cal tancar sessió SSH i tornar a entrar.

Comprovar:

```bash
docker --version
docker compose version
docker ps
```

## Crear estructura del projecte

```bash
sudo mkdir -p /srv/call-ai
sudo chown -R "$USER":"$USER" /srv/call-ai

mkdir -p /srv/call-ai/{audio_in,audio_archive,tmp_wav,transcripts,analysis,reports,scripts,db/init,logs,backups}
```

Estructura esperada:

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
│   └── init/
├── logs/
└── backups/
```

## Crear `.env`

Copiar l'exemple:

```bash
cp .env.example /srv/call-ai/.env
```

Editar:

```bash
nano /srv/call-ai/.env
```

Valors importants:

```bash
CALL_AI_BASE=/srv/call-ai

POSTGRES_DB=call_ai
POSTGRES_USER=call_ai
POSTGRES_PASSWORD=canvia_aquesta_contrasenya
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

OLLAMA_URL=http://192.168.1.9:11434
OLLAMA_MODEL=qwen3:8b

WHISPER_MODEL=medium
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_LANGUAGE=es
WHISPER_VAD=false

ASSISTENCIA_VALUE=34930185139
```

Generar contrasenya segura:

```bash
PASS="$(openssl rand -base64 32)"
sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$PASS|" /srv/call-ai/.env
```

## Copiar fitxers del projecte

Des del repositori:

```bash
cp compose.yaml /srv/call-ai/
cp -r db/init/* /srv/call-ai/db/init/
cp -r scripts/* /srv/call-ai/scripts/
chmod +x /srv/call-ai/scripts/*
```

## Arrencar PostgreSQL

```bash
cd /srv/call-ai
docker compose up -d
```

Comprovar:

```bash
docker ps
docker logs call-ai-postgres --tail=80
```

## Crear entorn Python

```bash
cd /srv/call-ai

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip setuptools wheel

pip install \
  psycopg2-binary \
  python-dotenv \
  requests \
  faster-whisper
```

Validar:

```bash
python -c "import psycopg2; import dotenv; import requests; from faster_whisper import WhisperModel; print('Python OK')"
```

## Provar BBDD

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

Dins PostgreSQL:

```sql
\dt
\dv
SELECT * FROM import_batches;
\q
```

## Crear primer lot

```bash
/srv/call-ai/scripts/psql-call-ai.sh
```

```sql
INSERT INTO import_batches
(name, batch_type, period_start, period_end, source_folder, notes)
VALUES
('Prova inicial', 'test', CURRENT_DATE, CURRENT_DATE, '/srv/call-ai/audio_in', 'Primer lot de prova')
RETURNING id, name, created_at;
```

Sortir:

```sql
\q
```

## Provar connexió amb Ollama

Des de Debian:

```bash
cd /srv/call-ai
set -a
source .env
set +a

curl "$OLLAMA_URL/api/tags"
```

Prova de xat:

```bash
curl "$OLLAMA_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3:8b",
    "stream": false,
    "messages": [
      {
        "role": "user",
        "content": "Respon només amb OK"
      }
    ]
  }'
```

## Instal·lació systemd

Copiar els fitxers systemd si existeixen o crear-los manualment.

Servei:

```bash
sudo nano /etc/systemd/system/call-ai-process-all.service
```

```ini
[Unit]
Description=Call-AI processa totes les trucades pendents
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=sommob
WorkingDirectory=/srv/call-ai
Environment=BATCH_SIZE=10
ExecStart=/srv/call-ai/scripts/process_all_pending.sh
TimeoutStartSec=infinity
```

Timer:

```bash
sudo nano /etc/systemd/system/call-ai-process-all.timer
```

```ini
[Unit]
Description=Executa Call-AI cada hora per processar trucades pendents

[Timer]
OnBootSec=10min
OnUnitActiveSec=1h
Persistent=true
Unit=call-ai-process-all.service

[Install]
WantedBy=timers.target
```

Activar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now call-ai-process-all.timer
```

Comprovar:

```bash
systemctl list-timers | grep call-ai
sudo systemctl status call-ai-process-all.timer --no-pager
```

## Prova final

Registrar àudios:

```bash
/srv/call-ai/scripts/register_audio_files.py 1
```

Processar pendents:

```bash
/srv/call-ai/scripts/process_all_pending.sh
```

Generar informe:

```bash
/srv/call-ai/scripts/make_monthly_package.sh 2026-05
```
