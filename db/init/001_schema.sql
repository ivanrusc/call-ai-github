CREATE EXTENSION IF NOT EXISTS vector;

-- ==========================
-- LOTS D'IMPORTACIÓ
-- ==========================

CREATE TABLE IF NOT EXISTS import_batches (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    batch_type TEXT NOT NULL DEFAULT 'manual',
    period_start DATE,
    period_end DATE,
    source_folder TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ==========================
-- TRUCADES
-- ==========================

CREATE TABLE IF NOT EXISTS calls (
    id BIGSERIAL PRIMARY KEY,
    batch_id BIGINT REFERENCES import_batches(id) ON DELETE SET NULL,

    original_filename TEXT NOT NULL,
    original_path TEXT NOT NULL UNIQUE,
    archived_path TEXT,
    wav_temp_path TEXT,

    service_type TEXT,
    -- assistencia / oficina

    call_date DATE,
    call_datetime TIMESTAMPTZ,

    duration_seconds NUMERIC(10,2),

    status TEXT NOT NULL DEFAULT 'imported',
    -- imported, transcribing, transcribed, analyzing, analyzed, error, needs_review

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ==========================
-- TRANSCRIPCIONS
-- ==========================

CREATE TABLE IF NOT EXISTS transcripts (
    id BIGSERIAL PRIMARY KEY,
    call_id BIGINT NOT NULL REFERENCES calls(id) ON DELETE CASCADE,

    language TEXT,
    language_probability NUMERIC(6,5),

    transcript_text TEXT NOT NULL,
    transcript_text_redacted TEXT,

    srt_path TEXT,
    transcript_json_path TEXT,

    whisper_model TEXT,
    processing_seconds NUMERIC(10,2),

    search_vector TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(transcript_text, ''))
    ) STORED,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ==========================
-- ANÀLISI GENERAL DE LA TRUCADA
-- ==========================

CREATE TABLE IF NOT EXISTS call_analysis (
    id BIGSERIAL PRIMARY KEY,
    call_id BIGINT NOT NULL REFERENCES calls(id) ON DELETE CASCADE,

    resum_general TEXT,
    idioma TEXT,

    model TEXT,
    ollama_url TEXT,
    processing_seconds NUMERIC(10,2),

    raw_json JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ==========================
-- MOTIUS / CONSULTES
-- Una trucada pot tenir 1 o més consultes
-- ==========================

CREATE TABLE IF NOT EXISTS call_motives (
    id BIGSERIAL PRIMARY KEY,

    call_id BIGINT NOT NULL REFERENCES calls(id) ON DELETE CASCADE,

    service_type TEXT NOT NULL,
    -- assistencia / oficina

    call_date DATE,

    consulta_num INTEGER NOT NULL DEFAULT 1,

    motiu_original TEXT NOT NULL,
    motiu_agrupat TEXT NOT NULL,

    resolucio TEXT,
    -- resolta / no resolta / pendent / transferida / informativa / desconeguda

    es_emergencia BOOLEAN NOT NULL DEFAULT false,

    es_reserva BOOLEAN NOT NULL DEFAULT false,
    reserva_finalitzada BOOLEAN,
    motiu_reserva_no_finalitzada TEXT,

    es_fallada_punt_carrega BOOLEAN NOT NULL DEFAULT false,

    accio_recomanada TEXT,

    confianca_classificacio NUMERIC(4,2),

    raw_item JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ==========================
-- PARAULES CLAU
-- ==========================

CREATE TABLE IF NOT EXISTS call_keywords (
    id BIGSERIAL PRIMARY KEY,

    call_id BIGINT NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    motive_id BIGINT REFERENCES call_motives(id) ON DELETE CASCADE,

    service_type TEXT NOT NULL,
    call_date DATE,

    keyword TEXT NOT NULL,
    keyword_normalized TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ==========================
-- DADES IDENTIFICATIVES
-- ==========================

CREATE TABLE IF NOT EXISTS call_identifiers (
    id BIGSERIAL PRIMARY KEY,

    call_id BIGINT NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    motive_id BIGINT REFERENCES call_motives(id) ON DELETE SET NULL,

    service_type TEXT NOT NULL,
    call_date DATE,

    identifier_type TEXT NOT NULL,
    -- nom, cognoms, nom_complet, dni_nie, telefon, email,
    -- matricula, adreca, numero_soci, numero_client,
    -- numero_reserva, altre

    identifier_value TEXT NOT NULL,
    identifier_value_normalized TEXT,

    confidence NUMERIC(4,2),

    context_fragment TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ==========================
-- GRUPS DE TRUCADES
-- ==========================

CREATE TABLE IF NOT EXISTS call_groups (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    group_type TEXT NOT NULL DEFAULT 'manual',
    -- manual, tema, mensual, diaria, campanya, revisio

    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS call_group_members (
    group_id BIGINT NOT NULL REFERENCES call_groups(id) ON DELETE CASCADE,
    call_id BIGINT NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (group_id, call_id)
);

-- ==========================
-- ÍNDEXS
-- ==========================

CREATE INDEX IF NOT EXISTS idx_calls_batch_id
ON calls(batch_id);

CREATE INDEX IF NOT EXISTS idx_calls_status
ON calls(status);

CREATE INDEX IF NOT EXISTS idx_calls_service_type
ON calls(service_type);

CREATE INDEX IF NOT EXISTS idx_calls_call_date
ON calls(call_date);

CREATE INDEX IF NOT EXISTS idx_transcripts_call_id
ON transcripts(call_id);

CREATE INDEX IF NOT EXISTS idx_transcripts_search_vector
ON transcripts USING GIN(search_vector);

CREATE INDEX IF NOT EXISTS idx_call_motives_call_id
ON call_motives(call_id);

CREATE INDEX IF NOT EXISTS idx_call_motives_service_type
ON call_motives(service_type);

CREATE INDEX IF NOT EXISTS idx_call_motives_call_date
ON call_motives(call_date);

CREATE INDEX IF NOT EXISTS idx_call_motives_motiu_agrupat
ON call_motives(motiu_agrupat);

CREATE INDEX IF NOT EXISTS idx_call_motives_emergencia
ON call_motives(es_emergencia);

CREATE INDEX IF NOT EXISTS idx_call_motives_reserva
ON call_motives(es_reserva);

CREATE INDEX IF NOT EXISTS idx_call_motives_punt_carrega
ON call_motives(es_fallada_punt_carrega);

CREATE INDEX IF NOT EXISTS idx_call_keywords_keyword
ON call_keywords(keyword_normalized);

CREATE INDEX IF NOT EXISTS idx_call_keywords_service_type
ON call_keywords(service_type);

CREATE INDEX IF NOT EXISTS idx_call_keywords_call_date
ON call_keywords(call_date);

CREATE INDEX IF NOT EXISTS idx_call_identifiers_call_id
ON call_identifiers(call_id);

CREATE INDEX IF NOT EXISTS idx_call_identifiers_type
ON call_identifiers(identifier_type);

CREATE INDEX IF NOT EXISTS idx_call_identifiers_value_normalized
ON call_identifiers(identifier_value_normalized);

CREATE INDEX IF NOT EXISTS idx_call_identifiers_service_type
ON call_identifiers(service_type);

CREATE INDEX IF NOT EXISTS idx_call_identifiers_call_date
ON call_identifiers(call_date);

CREATE INDEX IF NOT EXISTS idx_call_group_members_group
ON call_group_members(group_id);

CREATE INDEX IF NOT EXISTS idx_call_group_members_call
ON call_group_members(call_id);
