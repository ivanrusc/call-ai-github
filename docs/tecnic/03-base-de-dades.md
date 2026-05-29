######
# Base de dades Call-AI

## Motor

El sistema utilitza PostgreSQL amb pgvector.

PostgreSQL guarda:

- Metadades de trucades.
- Transcripcions.
- Anàlisi general.
- Motius detectats.
- Paraules clau.
- Identificadors personals detectats.
- Grups de trucades.
- Lots d'importació.

Els àudios originals no es guarden dins PostgreSQL. Es guarden com a fitxers al disc.

## Taules principals

### `import_batches`

Representa un lot d'importació.

Exemples:

```text
Prova inicial
Import inicial maig 2026
Import diari 2026-05-29
````

Camps importants:

```text
id
name
batch_type
period_start
period_end
source_folder
notes
created_at
```

### `calls`

Una fila per cada trucada.

Camps importants:

```text
id
batch_id
original_filename
original_path
archived_path
wav_temp_path
service_type
call_date
call_datetime
duration_seconds
status
error_message
created_at
updated_at
```

Valors de `status`:

```text
imported      trucada registrada però no transcrita
transcribing  transcripció en curs
transcribed   transcripció feta
analyzing     anàlisi en curs
analyzed      anàlisi feta
error         error en algun pas
needs_review  necessita revisió manual
```

### `transcripts`

Transcripció completa de cada trucada.

Camps importants:

```text
call_id
language
language_probability
transcript_text
transcript_text_redacted
srt_path
transcript_json_path
whisper_model
processing_seconds
search_vector
```

`search_vector` permet fer cerca de text dins transcripcions.

### `call_analysis`

Anàlisi general de la trucada.

Camps importants:

```text
call_id
resum_general
idioma
model
ollama_url
processing_seconds
raw_json
```

### `call_motives`

Taula principal per estadístiques.

Una trucada pot tenir més d'una consulta.
Per tant, una trucada pot tenir més d'una fila a `call_motives`.

Camps importants:

```text
call_id
service_type
call_date
consulta_num
motiu_original
motiu_agrupat
resolucio
es_emergencia
es_reserva
reserva_finalitzada
motiu_reserva_no_finalitzada
es_fallada_punt_carrega
accio_recomanada
confianca_classificacio
raw_item
```

### `call_keywords`

Paraules clau generades per consulta.

Camps importants:

```text
call_id
motive_id
service_type
call_date
keyword
keyword_normalized
```

### `call_identifiers`

Dades personals o identificatives detectades.

Aquesta taula és sensible.

Camps importants:

```text
call_id
motive_id
service_type
call_date
identifier_type
identifier_value
identifier_value_normalized
confidence
context_fragment
```

Tipus possibles:

```text
nom
cognoms
nom_complet
dni_nie
telefon
email
matricula
adreca
numero_soci
numero_client
numero_reserva
altre
```

### `call_groups`

Grups manuals o automàtics de trucades.

### `call_group_members`

Relació entre grups i trucades.

## Regles de negoci

### Assistència / oficina

Es calcula a partir del nom del fitxer:

```text
Si el nom conté 34930185139 → assistencia
Si no → oficina
```

El valor configurable està a `.env`:

```bash
ASSISTENCIA_VALUE=34930185139
```

### Data de trucada

La data es calcula a partir de la subcarpeta:

```text
/srv/call-ai/audio_in/2026-05-29/trucada.mp3
```

Resultat:

```text
call_date = 2026-05-29
```

## Consultes SQL útils

### Estat general

```sql
SELECT status, COUNT(*)
FROM calls
GROUP BY status
ORDER BY status;
```

### Últimes trucades

```sql
SELECT
    id,
    original_filename,
    service_type,
    call_date,
    duration_seconds,
    status,
    updated_at
FROM calls
ORDER BY updated_at DESC
LIMIT 20;
```

### Motius detectats

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
ORDER BY c.id DESC, m.consulta_num
LIMIT 50;
```

### Resum assistència

```sql
SELECT *
FROM view_resum_assistencia;
```

### Resum oficina

```sql
SELECT *
FROM view_resum_oficina;
```

### Trucades per dia

```sql
SELECT *
FROM view_trucades_per_dia;
```

### Paraules clau

```sql
SELECT *
FROM view_keywords
LIMIT 50;
```

### Identificadors detectats

```sql
SELECT
    identifier_type,
    identifier_value,
    confidence,
    context_fragment
FROM call_identifiers
ORDER BY created_at DESC
LIMIT 50;
```

## Vistes

### `view_motius_repetits`

Agrupa motius per:

```text
service_type
motiu_agrupat
resolucio
es_emergencia
```

### `view_trucades_per_dia`

Compta trucades per dia i tipus de servei.

### `view_consultes_per_dia`

Compta consultes/motius per dia i tipus de servei.

### `view_resum_assistencia`

Motius habituals d'assistència.

### `view_resum_oficina`

Motius habituals d'oficina.

### `view_reserves_no_finalitzades`

Agrupa motius pels quals no s'ha pogut finalitzar una reserva.

### `view_keywords`

Paraules clau més repetides.

### `view_identificadors_detectats`

Tipus d'identificadors detectats per servei.

## Reprocessar una trucada

Per tornar a analitzar una trucada:

```bash
/srv/call-ai/scripts/analyze_call.py ID_TRUCADA
```

L'script elimina l'anàlisi anterior i la substitueix.

Per tornar a transcriure:

```bash
/srv/call-ai/scripts/transcribe_call.py ID_TRUCADA
```

## Netejar una trucada concreta

Exemple per eliminar l'anàlisi d'una trucada:

```sql
DELETE FROM call_identifiers WHERE call_id = 1;
DELETE FROM call_keywords WHERE call_id = 1;
DELETE FROM call_motives WHERE call_id = 1;
DELETE FROM call_analysis WHERE call_id = 1;

UPDATE calls
SET status = 'transcribed',
    error_message = NULL,
    updated_at = now()
WHERE id = 1;
```

## Esborrar una trucada completament

Atenció: això elimina també transcripcions i anàlisis relacionades.

```sql
DELETE FROM calls
WHERE id = 1;
```

Perquè les taules relacionades tenen `ON DELETE CASCADE`.

## Còpia de seguretat de la BBDD

Veure document:

```text
docs/tecnic/05-backups.md
```
