# Privacitat i tractament de dades — Call-AI

## 1. Objectiu

Aquest document explica com el sistema Call-AI tracta la privacitat i les dades identificatives.

Call-AI processa trucades gravades i pot detectar informació personal o identificativa que aparegui dins la conversa.

## 2. Funcionament local

El sistema està dissenyat per funcionar 100% en local dins la infraestructura del client.

Això vol dir:

```text
- els àudios es guarden al servidor del client
- les transcripcions es guarden al servidor del client
- la base de dades està al servidor del client
- els informes es generen al servidor del client
- l'anàlisi amb IA es fa dins la xarxa local
````

No és necessari enviar trucades ni transcripcions a serveis externs.

## 3. Components locals

El sistema utilitza dos components principals:

```text
Servidor Debian:
  - àudios
  - base de dades
  - transcripcions
  - informes
  - scripts de procés

Mac mini M4:
  - Ollama
  - model local d'anàlisi
```

La comunicació entre aquests equips queda dins la xarxa local del client.

## 4. Tipus de dades tractades

El sistema pot tractar:

```text
- veu gravada
- transcripció de la trucada
- resum de la conversa
- motiu de la trucada
- resolució
- paraules clau
- dades identificatives
```

## 5. Dades identificatives que es poden detectar

Si apareixen a la trucada, el sistema pot detectar dades com:

```text
nom
cognoms
nom complet
DNI/NIE
telèfon
email
matrícula
adreça
número de soci
número de client
número de reserva
altres identificadors
```

Aquestes dades no s'inventen.

Només es guarden si apareixen a la transcripció i el sistema les detecta.

## 6. Separació entre dades estadístiques i dades identificatives

El sistema separa dos tipus d'informació.

### Dades estadístiques

Exemples:

```text
motiu de trucada
resolució
emergència sí/no
assistència/oficina
reserva finalitzada sí/no
fallada punt de càrrega sí/no
paraules clau
```

Aquestes dades són les que s'utilitzen habitualment en els informes.

### Dades identificatives

Exemples:

```text
nom
DNI
telèfon
email
número de reserva
```

Aquestes dades es guarden separadament i només s'han d'utilitzar quan sigui necessari.

## 7. Informes normals

Els informes normals no inclouen dades identificatives personals.

La generació normal produeix fitxers estadístics.

Exemple:

```text
call-ai-2026-05.zip
```

Aquest paquet està pensat per revisió general.

## 8. Informes sensibles

Si es genera un informe amb dades identificatives, el fitxer queda marcat com a sensible.

Exemples:

```text
09_identificadors_detectats_SENSIBLE.csv
call-ai-2026-05-SENSIBLE.zip
```

Aquests fitxers només s'han de compartir amb persones autoritzades.

## 9. Recomanacions d'accés

Es recomana diferenciar perfils d'accés.

### Perfil estadístic

Pot veure:

```text
- informes generals
- motius agrupats
- resum assistència
- resum oficina
- paraules clau
- trucades per dia
```

No hauria de veure:

```text
- DNI
- telèfon
- email
- transcripcions completes amb dades personals
```

### Perfil supervisor

Pot veure:

```text
- informes generals
- transcripcions
- dades identificatives quan calgui
- fitxers sensibles
```

### Perfil administrador

Pot gestionar:

```text
- configuració
- backups
- usuaris
- manteniment
- restauracions
```

## 10. Conservació de dades

La política de conservació l'ha de definir el client.

Cal decidir durant quant temps es conserven:

```text
- àudios originals
- transcripcions
- informes
- dades identificatives
- backups
```

Recomanació general:

```text
Conservar només el temps necessari per a la finalitat del servei.
```

## 11. Backups

Els backups poden contenir dades personals.

Per tant, s'han de protegir adequadament.

Recomanacions:

```text
- guardar backups en ubicació segura
- restringir accés
- xifrar si surten del servidor
- provar restauracions periòdicament
- eliminar backups antics segons política de retenció
```

## 12. Exportació de fitxers

Abans d'enviar un fitxer fora del servidor, cal revisar si és sensible.

Fitxers normals:

```text
call-ai-2026-05.zip
```

Fitxers sensibles:

```text
call-ai-2026-05-SENSIBLE.zip
09_identificadors_detectats_SENSIBLE.csv
```

Els fitxers sensibles no s'han d'enviar per canals no segurs.

## 13. GitHub i repositoris

No s'han de pujar mai a GitHub:

```text
.env
àudios reals
transcripcions reals
informes reals
backups
base de dades real
fitxers amb dades personals
fitxers marcats com SENSIBLE
```

El repositori del projecte només ha de contenir:

```text
- codi
- scripts
- documentació
- exemples sense dades reals
- fitxers de configuració d'exemple
```

## 14. Errors possibles de detecció

El sistema pot equivocar-se.

Pot passar que:

```text
- no detecti una dada identificativa
- detecti una dada que no ho és
- interpreti malament una paraula per error de transcripció
```

Per això els fitxers sensibles s'han de revisar amb criteri humà quan s'utilitzin.

## 15. Transcripció anonimitzada

El sistema pot generar una versió anonimitzada de la transcripció.

Exemple:

```text
La persona [NOM_COMPLET] truca per consultar la reserva [NUMERO_RESERVA].
```

Aquesta versió és més adequada per informes generals.

## 16. Bones pràctiques

```text
- utilitzar informes normals sempre que sigui possible
- generar informes sensibles només quan calgui
- limitar l'accés a dades identificatives
- revisar permisos del servidor
- no enviar fitxers sensibles per email sense protecció
- definir política de conservació
- fer backups protegits
```

## 17. Responsabilitat del client

El client és responsable de definir:

```text
- qui pot accedir al sistema
- durant quant temps es conserven les dades
- qui pot veure dades identificatives
- com es comparteixen informes
- quan s'han d'esborrar dades antigues
```

## 18. Resum

Call-AI està pensat per reduir riscos perquè funciona en local.

Tot i així, com que tracta trucades i dades identificatives, cal gestionar l'accés, la conservació, els backups i els informes sensibles amb cura.

La regla pràctica és:

```text
Informes generals → sense dades identificatives
Informes sensibles → només per persones autoritzades
```
