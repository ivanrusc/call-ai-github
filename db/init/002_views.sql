CREATE OR REPLACE VIEW view_motius_repetits AS
SELECT
    service_type,
    motiu_agrupat,
    resolucio,
    es_emergencia,
    COUNT(*) AS vegades
FROM call_motives
GROUP BY
    service_type,
    motiu_agrupat,
    resolucio,
    es_emergencia
ORDER BY service_type, vegades DESC;


CREATE OR REPLACE VIEW view_trucades_per_dia AS
SELECT
    call_date,
    service_type,
    COUNT(*) AS total_trucades
FROM calls
WHERE call_date IS NOT NULL
GROUP BY call_date, service_type
ORDER BY call_date DESC, service_type;


CREATE OR REPLACE VIEW view_consultes_per_dia AS
SELECT
    call_date,
    service_type,
    COUNT(*) AS total_consultes
FROM call_motives
WHERE call_date IS NOT NULL
GROUP BY call_date, service_type
ORDER BY call_date DESC, service_type;


CREATE OR REPLACE VIEW view_resum_assistencia AS
SELECT
    motiu_agrupat,
    COUNT(*) AS vegades,
    COUNT(*) FILTER (WHERE es_emergencia = true) AS emergències,
    COUNT(*) FILTER (WHERE es_fallada_punt_carrega = true) AS fallades_punt_carrega
FROM call_motives
WHERE service_type = 'assistencia'
GROUP BY motiu_agrupat
ORDER BY vegades DESC;


CREATE OR REPLACE VIEW view_resum_oficina AS
SELECT
    motiu_agrupat,
    COUNT(*) AS vegades,
    COUNT(*) FILTER (WHERE es_emergencia = true) AS emergències,
    COUNT(*) FILTER (WHERE es_reserva = true) AS consultes_reserva,
    COUNT(*) FILTER (WHERE reserva_finalitzada = false) AS reserves_no_finalitzades
FROM call_motives
WHERE service_type = 'oficina'
GROUP BY motiu_agrupat
ORDER BY vegades DESC;


CREATE OR REPLACE VIEW view_reserves_no_finalitzades AS
SELECT
    service_type,
    motiu_reserva_no_finalitzada,
    COUNT(*) AS vegades,
    COUNT(*) FILTER (WHERE es_fallada_punt_carrega = true) AS fallades_punt_carrega
FROM call_motives
WHERE es_reserva = true
  AND reserva_finalitzada = false
GROUP BY service_type, motiu_reserva_no_finalitzada
ORDER BY vegades DESC;


CREATE OR REPLACE VIEW view_keywords AS
SELECT
    service_type,
    keyword_normalized,
    COUNT(*) AS vegades
FROM call_keywords
GROUP BY service_type, keyword_normalized
ORDER BY service_type, vegades DESC;


CREATE OR REPLACE VIEW view_identificadors_detectats AS
SELECT
    identifier_type,
    service_type,
    COUNT(*) AS vegades
FROM call_identifiers
GROUP BY identifier_type, service_type
ORDER BY service_type, vegades DESC;
