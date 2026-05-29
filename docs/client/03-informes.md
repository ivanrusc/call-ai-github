# Informes Call-AI

## 1. Objectiu dels informes

Els informes permeten consultar i resumir l'activitat de trucades d'un període concret.

Normalment es generen per mesos.

Exemple:

```text
2026-05
````

L'objectiu és veure:

```text
- quantes trucades hi ha hagut
- quantes són d'assistència
- quantes són d'oficina
- quins motius es repeteixen més
- quantes emergències hi ha
- quantes reserves no s'han finalitzat
- quantes incidències són de punt de càrrega
- quines paraules clau apareixen més
```

## 2. On es guarden els informes?

Els informes es guarden a:

```text
/srv/call-ai/reports/
```

Cada mes té la seva carpeta.

Exemple:

```text
/srv/call-ai/reports/2026-05/
```

Dins aquesta carpeta hi ha CSVs i un informe resum.

## 3. Fitxers generats

Per cada mes es poden generar aquests fitxers:

```text
01_trucades.csv
02_motius_repetits.csv
03_motius_detall.csv
04_trucades_per_dia.csv
05_paraules_clau.csv
06_resum_assistencia.csv
07_resum_oficina.csv
08_reserves_no_finalitzades.csv
09_identificadors_detectats_SENSIBLE.csv
informe_resum.md
```

El fitxer d'identificadors personals només es genera si es demana expressament.

## 4. `informe_resum.md`

És l'informe principal.

Inclou:

```text
- resum general
- total de trucades
- total d'assistència
- total d'oficina
- total de consultes detectades
- emergències
- reserves no finalitzades
- fallades de punt de càrrega
- motius més habituals d'assistència
- motius més habituals d'oficina
- trucades per dia
- paraules clau més habituals
```

Aquest fitxer és útil per lectura ràpida.

## 5. `01_trucades.csv`

Conté una línia per cada trucada.

Columnes habituals:

```text
id
call_date
service_type
original_filename
duration_seconds
status
created_at
updated_at
resum_general
idioma
```

Serveix per veure totes les trucades processades del mes.

## 6. `02_motius_repetits.csv`

Agrupa motius repetits.

Columnes habituals:

```text
service_type
motiu_agrupat
resolucio
es_emergencia
vegades
consultes_reserva
reserves_no_finalitzades
fallades_punt_carrega
```

És un dels fitxers més importants.

Serveix per respondre preguntes com:

```text
Quin és el motiu més habitual a assistència?
Quin és el motiu més habitual a oficina?
Quantes vegades es repeteix una incidència?
Quantes són emergències?
```

## 7. `03_motius_detall.csv`

Conté el detall de cada consulta detectada.

Una trucada pot tenir més d'una línia si conté més d'una consulta.

Columnes habituals:

```text
call_id
call_date
service_type
original_filename
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
```

Aquest fitxer serveix per revisar casos concrets.

## 8. `04_trucades_per_dia.csv`

Mostra quantes trucades hi ha hagut cada dia.

Columnes:

```text
call_date
assistencia
oficina
total
```

Exemple:

```text
2026-05-01 ; 12 ; 31 ; 43
2026-05-02 ; 9  ; 28 ; 37
```

Serveix per veure volum diari.

## 9. `05_paraules_clau.csv`

Agrupa paraules clau detectades.

Columnes:

```text
service_type
keyword_normalized
vegades
```

Exemples de paraules clau:

```text
reserva
factura
punt de càrrega
vehicle
app
pagament
targeta
quilòmetres
```

Serveix per detectar temes recurrents.

## 10. `06_resum_assistencia.csv`

Resum específic de trucades d'assistència.

Columnes habituals:

```text
motiu_agrupat
vegades
emergències
consultes_reserva
reserves_no_finalitzades
fallades_punt_carrega
```

Serveix per veure què passa a assistència.

## 11. `07_resum_oficina.csv`

Resum específic de trucades d'oficina.

Columnes habituals:

```text
motiu_agrupat
vegades
emergències
consultes_reserva
reserves_no_finalitzades
fallades_punt_carrega
```

Serveix per veure què passa a oficina.

## 12. `08_reserves_no_finalitzades.csv`

Agrupa els motius pels quals una reserva no s'ha pogut finalitzar.

Columnes:

```text
service_type
motiu_reserva_no_finalitzada
vegades
fallades_punt_carrega
```

És útil per detectar problemes recurrents en el procés de reserva.

## 13. `09_identificadors_detectats_SENSIBLE.csv`

Aquest fitxer és sensible.

Només es genera si es demana expressament.

Pot contenir:

```text
nom
cognoms
DNI/NIE
telèfon
email
matrícula
número de soci
número de client
número de reserva
altres identificadors
```

Aquest fitxer no s'ha de compartir amb persones no autoritzades.

## 14. Paquets ZIP

El sistema pot generar un paquet ZIP mensual.

Exemple normal:

```text
call-ai-2026-05.zip
```

Exemple amb dades sensibles:

```text
call-ai-2026-05-SENSIBLE.zip
```

Els ZIPs es guarden a:

```text
/srv/call-ai/reports/exports/
```

## 15. Diferència entre ZIP normal i ZIP sensible

### ZIP normal

No inclou identificadors personals.

Pensat per informes generals.

Exemple:

```text
call-ai-2026-05.zip
```

### ZIP sensible

Inclou dades identificatives.

Només per persones autoritzades.

Exemple:

```text
call-ai-2026-05-SENSIBLE.zip
```

## 16. Com obrir els CSV

Els CSVs utilitzen separador:

```text
;
```

Això facilita obrir-los amb LibreOffice o Excel en configuració europea.

Si s'obre amb LibreOffice:

```text
1. Obrir fitxer CSV.
2. Seleccionar separador punt i coma.
3. Codificació UTF-8.
```

## 17. Interpretació recomanada

Per fer una revisió mensual, es recomana mirar en aquest ordre:

```text
1. informe_resum.md
2. 06_resum_assistencia.csv
3. 07_resum_oficina.csv
4. 02_motius_repetits.csv
5. 04_trucades_per_dia.csv
6. 03_motius_detall.csv
```

Només revisar el fitxer sensible si hi ha una necessitat concreta.

## 18. Indicadors útils

Alguns indicadors interessants:

```text
- motiu més repetit a assistència
- motiu més repetit a oficina
- percentatge d'emergències
- reserves no finalitzades
- incidències de punt de càrrega
- dies amb més trucades
- paraules clau més repetides
- trucades pendents o no resoltes
```

## 19. Limitacions dels informes

Els informes depenen de:

```text
- qualitat de l'àudio
- qualitat de la transcripció
- claredat de la conversa
- correcta classificació automàtica
```

Poden existir errors.

Els resultats s'han d'entendre com una ajuda a l'anàlisi, no com una auditoria manual perfecta.

## 20. Recomanació d'ús

Recomanat fer una revisió mensual amb:

```text
- responsable d'oficina
- responsable d'assistència
- persona encarregada de processos
```

Objectiu:

```text
1. Detectar motius repetits.
2. Revisar incidències crítiques.
3. Identificar problemes de procés.
4. Millorar documentació interna.
5. Reduir trucades repetitives.
```
