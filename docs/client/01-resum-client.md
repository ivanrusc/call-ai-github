# Sistema local d'analisi de trucades

## Objectiu

El sistema permet transformar trucades gravades en informació útil per a la gestió del servei.

A partir de les gravacions, el sistema genera:

- Transcripció de la trucada.
- Motiu o motius de la trucada.
- Resolució.
- Indicació d'emergència.
- Separació entre assistència i oficina.
- Paraules clau.
- Dades identificatives detectades.
- Informes mensuals.

## Funcionament general

Les trucades es deixen en una carpeta del servidor.

El sistema les processa automàticament i genera informes mensuals.

## Separació assistència / oficina

El sistema classifica les trucades segons el nom de l'arxiu:

- Si el nom conté `34930185139`, es considera assistència.
- Si no el conté, es considera oficina.

## Data de la trucada

La data es detecta segons la subcarpeta on es troba l'arxiu.

Exemple:

```text
/srv/call-ai/audio_in/2026-05-29/trucada.mp3
```
La data serà:

2026-05-29
Consultes múltiples

Una mateixa trucada pot contenir més d'una consulta.

En aquest cas, el sistema separa cada consulta en línies diferents per poder comptar correctament els motius.

Privacitat

El sistema funciona 100% en local.

No s'envien àudios ni transcripcions a serveis externs.

Les dades identificatives es poden exportar en un fitxer separat i marcat com a sensible.
