# Seguretat i protecció de dades

## Objectiu

Call-AI processa trucades gravades.

Les trucades poden contenir:

```text
veu
nom
cognoms
DNI/NIE
telèfon
email
matrícula
adreça
número de soci
número de client
número de reserva
altres dades identificatives
````

Per tant, el sistema s'ha de tractar com un sistema amb dades personals.

## Principi general

El sistema està dissenyat per funcionar 100% en local.

```text
Àudios            local
Transcripcions    local
BBDD              local
Anàlisi IA        local
Informes          local
```

No s'han d'enviar àudios ni transcripcions a serveis externs.

## Components locals

### Debian

Servidor principal:

```text
/srv/call-ai
PostgreSQL
scripts
informes
backups
```

### Mac mini M4

Servidor IA local:

```text
Ollama
qwen3:8b
```

El trànsit entre Debian i Mac mini ha de quedar dins la LAN del client.

## Dades sensibles

Taules sensibles:

```text
transcripts
call_identifiers
call_analysis.raw_json
```

Fitxers sensibles:

```text
audio_in/
audio_archive/
transcripts/
analysis/
reports/*SENSIBLE*
backups/
.env
```

## Separació de dades

El sistema separa:

```text
Dades estadístiques:
  motius
  resolució
  emergències
  paraules clau
  resum
  assistència/oficina

Dades identificatives:
  nom
  DNI/NIE
  telèfon
  email
  matrícula
  número de reserva
```

Les dades identificatives es guarden a:

```text
call_identifiers
```

## Informes

Per defecte, els informes mensuals no exporten identificadors personals.

Comanda normal:

```bash
/srv/call-ai/scripts/make_monthly_package.sh 2026-05
```

Amb dades sensibles:

```bash
/srv/call-ai/scripts/make_monthly_package.sh 2026-05 yes
```

Aquesta segona comanda genera:

```text
09_identificadors_detectats_SENSIBLE.csv
call-ai-YYYY-MM-SENSIBLE.zip
```

## Fitxers que no s'han de pujar a GitHub

```text
.env
audio_in/
audio_archive/
tmp_wav/
transcripts/
analysis/
reports/
logs/
backups/
db/postgres/
*.mp3
*.wav
*.m4a
*.aac
*.flac
*.ogg
*.wma
*SENSIBLE*
```

El repositori inclou `.gitignore` per evitar-ho.

## PostgreSQL

El contenidor PostgreSQL només publica port en local:

```yaml
ports:
  - "127.0.0.1:5432:5432"
```

Això evita accés directe des de la xarxa.

## Permisos recomanats

Directori:

```bash
sudo chown -R sommob:sommob /srv/call-ai
chmod 750 /srv/call-ai
```

Fitxer `.env`:

```bash
chmod 600 /srv/call-ai/.env
```

Backups:

```bash
chmod -R 700 /srv/call-ai/backups
```

## Accés al servidor

Recomanat:

```text
SSH amb clau
sense password si és possible
accés només des de LAN o VPN
usuari no-root
sudo controlat
```

## Ollama

Ollama al Mac mini ha d'escoltar només dins la LAN del client.

Exemple:

```text
OLLAMA_HOST=0.0.0.0:11434
```

Cal assegurar que:

```text
- no està exposat a Internet
- només accessible des de la LAN/VPN
- firewall macOS configurat si cal
```

Prova des de Debian:

```bash
curl http://192.168.1.9:11434/api/tags
```

## Minimització

Guardar només el necessari.

Recomanació:

```text
Guardar MP3 original: sí
Guardar TXT: sí
Guardar JSON: sí
Guardar WAV temporal: no
Guardar informes sensibles: només si cal
```

Els WAV temporals es creen a:

```text
/srv/call-ai/tmp_wav/
```

i s'esborren després de transcriure.

## Retenció de dades

La política de retenció l'ha de decidir el client.

Opcions habituals:

```text
Àudios: 6-24 mesos
Transcripcions: 6-24 mesos
Informes estadístics: 24-60 mesos
Identificadors personals: el mínim necessari
Backups: segons política interna
```

## Exportació de dades sensibles

Abans d'entregar fitxers sensibles:

```text
1. Confirmar receptor autoritzat
2. Confirmar finalitat
3. Evitar enviament per canals insegurs
4. Xifrar si surt del servidor
5. Registrar entrega si cal
```

## Riscos principals

```text
- Pujar dades reals a GitHub
- Enviar informes sensibles per email sense xifrar
- Exposar PostgreSQL a xarxa
- Exposar Ollama a Internet
- Conservar dades més temps del necessari
- Donar accés a transcripcions completes a usuaris no autoritzats
```

## Bones pràctiques

```text
- Revisar .gitignore abans de cada commit
- No copiar .env al repositori
- No fer captures amb dades personals
- Fer backups xifrats
- Revisar permisos
- Separar informes normals i sensibles
- Provar restauracions
```

## Comprovar que no hi ha secrets al repositori

```bash
cd /srv/call-ai-github

find . -type f | sort

grep -R "POSTGRES_PASSWORD" . || true
grep -R "identifier_value" . || true
grep -R "dni" . || true
grep -R "telefon" . || true
```

Només haurien d'aparèixer exemples i documentació.

## Documentació per al client

Veure:

```text
docs/client/04-privacitat.md
```
