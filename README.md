# Call-AI Local 

Sistema local per importar, transcriure, analitzar i classificar trucades gravades.

## Objectiu

Aquest projecte permet:

- Registrar trucades en una base de dades PostgreSQL.
- Detectar si una trucada és d'assistència o oficina.
- Detectar la data de la trucada segons la subcarpeta.
- Transcriure àudios amb Whisper / faster-whisper en local.
- Analitzar transcripcions amb Ollama i un model LLM local.
- Separar diferents consultes dins una mateixa trucada.
- Agrupar motius semblants.
- Detectar emergències.
- Detectar reserves no finalitzades.
- Detectar incidències de punt de càrrega.
- Generar paraules clau.
- Detectar dades identificatives quan apareixen a la trucada.
- Generar informes mensuals en CSV i Markdown.
- Crear paquets ZIP mensuals per entregar.

## Arquitectura

```text
Debian VM / CT
  ├── PostgreSQL
  ├── àudios
  ├── STT Whisper
  ├── scripts de procés
  ├── informes
  └── exports

Mac mini M4
  └── Ollama + qwen3:8b
