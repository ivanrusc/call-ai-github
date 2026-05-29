# Manual d'usuari:  Call-AI

## 1. Què és Call-AI?

Call-AI és un sistema local que permet analitzar trucades gravades.

El sistema converteix les trucades en text, detecta el motiu de la trucada, classifica si és assistència o oficina, identifica si hi ha emergències, separa consultes diferents dins una mateixa trucada i genera informes mensuals.

## 2. Què fa el sistema?

A partir de cada trucada gravada, el sistema pot generar:

- Transcripció de la trucada.
- Resum general.
- Motiu o motius de la trucada.
- Resolució.
- Indicació de si és emergència.
- Indicació de si és una consulta de reserva.
- Indicació de si la reserva s'ha finalitzat o no.
- Detecció de fallades de punt de càrrega.
- Paraules clau.
- Dades identificatives detectades, si apareixen.
- Informes mensuals.

## 3. On s'han de deixar les trucades?

Les trucades s'han de deixar dins la carpeta:

```text
/srv/call-ai/audio_in/
````

S'han d'organitzar per data.

Exemple:

```text
/srv/call-ai/audio_in/2026-05-29/trucada_001.mp3
/srv/call-ai/audio_in/2026-05-29/trucada_002.mp3
/srv/call-ai/audio_in/2026-05-30/trucada_003.mp3
```

La subcarpeta indica la data de la trucada.

Per exemple:

```text
/srv/call-ai/audio_in/2026-05-29/trucada_001.mp3
```

El sistema interpretarà que la trucada és del dia:

```text
2026-05-29
```

## 4. Formats d'àudio admesos

El sistema pot treballar amb formats habituals com:

```text
.mp3
.wav
.m4a
.aac
.ogg
.flac
.wma
```

El format recomanat és:

```text
.mp3
```

## 5. Com sap el sistema si és assistència o oficina?

El sistema fa servir una regla basada en el nom del fitxer.

Si el nom del fitxer conté:

```text
34930185139
```

la trucada es classifica com:

```text
assistència
```

Si no conté aquest valor, es classifica com:

```text
oficina
```

Exemples:

```text
trucada_2_34930185139.mp3  → assistència
trucada_001.mp3            → oficina
```

## 6. Què passa si una trucada té més d'una consulta?

Una trucada pot contenir més d'una consulta.

Per exemple, una mateixa trucada pot parlar de:

```text
- una reserva
- una factura
- una modificació de dades
```

En aquest cas, el sistema separa cada consulta en una línia diferent dins l'informe de motius.

Això permet comptar correctament els temes més repetits.

## 7. Què és un motiu agrupat?

El sistema intenta agrupar motius semblants.

Per exemple, aquestes frases poden acabar dins el mateix grup:

```text
No pot acabar la reserva
No li deixa confirmar la reserva
Error al finalitzar la reserva
```

Motiu agrupat:

```text
Reserva no finalitzada
```

Un altre exemple:

```text
El punt de càrrega no funciona
El vehicle no carrega
Problema amb el carregador
```

Motiu agrupat:

```text
Incidència punt de càrrega
```

## 8. Què és la resolució?

La resolució indica com ha acabat la consulta.

Possibles valors:

```text
resolta
no resolta
pendent
transferida
informativa
desconeguda
```

Exemples:

```text
resolta      → la persona ha rebut resposta i no cal fer res més
pendent      → cal fer alguna acció posterior
transferida  → s'ha derivat a una altra persona o equip
no resolta   → no s'ha pogut solucionar
```

## 9. Què és una emergència?

El sistema marca una consulta com a emergència si detecta que la situació requereix atenció urgent.

Exemples possibles:

```text
- vehicle bloquejat
- persona no pot retornar el vehicle
- incidència greu amb el vehicle
- problema urgent d'assistència
```

Aquest camp ajuda a revisar trucades crítiques.

## 10. Què passa amb les reserves no finalitzades?

Si una trucada indica que no s'ha pogut finalitzar una reserva, el sistema intenta guardar:

```text
- que és una consulta de reserva
- que la reserva no s'ha finalitzat
- el motiu
- si està relacionat amb un punt de càrrega
```

Exemple:

```text
Motiu agrupat: Reserva no finalitzada
Motiu reserva no finalitzada: Error al punt de càrrega
Fallada punt de càrrega: sí
```

## 11. Dades identificatives

El sistema pot detectar dades que apareixen dins la trucada, com:

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

Aquestes dades es guarden separades de les estadístiques generals.

Els informes normals no inclouen aquestes dades per defecte.

## 12. Funcionament automàtic

El sistema pot funcionar automàticament.

Cada cert temps:

```text
1. Revisa si hi ha trucades noves.
2. Les registra a la base de dades.
3. Les transcriu.
4. Les analitza.
5. Guarda resultats.
```

Si un dia hi ha 30 trucades, processa 30.

Si un dia hi ha 50 trucades, processa 50.

Si no hi ha trucades noves, no fa res.

## 13. Informes mensuals

Els informes mensuals es generen per mes.

Exemple:

```text
Informe de maig de 2026
```

El sistema crea:

```text
- CSV de trucades
- CSV de motius repetits
- CSV de motius detallats
- CSV de trucades per dia
- CSV de paraules clau
- resum assistència
- resum oficina
- informe resum en Markdown
- paquet ZIP
```

## 14. Fitxers d'informe habituals

Els fitxers més importants són:

```text
informe_resum.md
02_motius_repetits.csv
03_motius_detall.csv
04_trucades_per_dia.csv
06_resum_assistencia.csv
07_resum_oficina.csv
```

## 15. Fitxers sensibles

Els fitxers que contenen dades identificatives apareixen marcats com:

```text
SENSIBLE
```

Exemple:

```text
09_identificadors_detectats_SENSIBLE.csv
call-ai-2026-05-SENSIBLE.zip
```

Aquests fitxers només s'han de compartir amb persones autoritzades.

## 16. Limitacions

El sistema fa una anàlisi automàtica basada en transcripció de veu.

Pot haver-hi errors si:

```text
- l'àudio té mala qualitat
- hi ha soroll de fons
- parlen dues persones alhora
- la trucada barreja idiomes
- la transcripció no és clara
- es diuen dades de manera confusa
```

Per aquest motiu, les dades importants s'han de revisar quan sigui necessari.

## 17. Ús recomanat

El sistema és especialment útil per:

```text
- veure motius més repetits
- detectar problemes recurrents
- separar assistència i oficina
- detectar incidències de reserva
- detectar emergències
- revisar fallades de punt de càrrega
- preparar informes mensuals
- millorar processos interns
```

## 18. Flux resumit

```text
Trucades gravades
  ↓
Carpeta per data
  ↓
Registre automàtic
  ↓
Transcripció
  ↓
Anàlisi
  ↓
Base de dades
  ↓
Informes mensuals
```
