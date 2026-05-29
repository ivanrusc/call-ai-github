# Arquitectura tècnica Call-AI

## Resum

Call-AI és un sistema local per processar trucades gravades.

La Debian actua com a servidor principal de dades i procés.

El Mac mini M4 actua com a servidor local d'IA per Ollama.

## Components

### Debian

- PostgreSQL amb pgvector
- Docker Compose
- Python
- faster-whisper
- ffmpeg
- scripts d'importació, transcripció, anàlisi i informes

### Mac mini M4

- Ollama
- Model qwen3:8b

## Carpetes principals

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
## Base de dades
 -  Taules principals:
import_batches
calls
transcripts
call_analysis
call_motives
call_keywords
call_identifiers
call_groups
call_group_members

## Flux
1. El client deixa udios a audio_in/YYYY-MM-DD/
2. register_audio_files.py registra els àudios a PostgreSQL
3. transcribe_call.py transcriu amb Whisper
4. analyze_call.py analitza amb Ollama
5. process_pending_calls.py processa lots
6. process_all_pending.sh processa tot el pendent
7. export_monthly_report.py genera CSV i informe
8. zip_monthly_report.py crea paquet ZIP

