# Plan 001 — Spike de metadatos IPTC/XMP

**Estado:** cerrado — se sustituye por la caption en el nombre del archivo.

**Objetivo inicial:** confirmar que `pyexiv2` lee la caption escrita por el iPhone desde los metadatos IPTC/XMP.

**Resultado del spike**
- `sample.HEIC` era un HEIC válido (ISO Media / HEIF).
- `pyexiv2` abría el archivo pero devolvía **0 claves EXIF, 0 IPTC y 0 XMP**.
- Inspección con Python puro: el XMP solo contenía `HDRGainMap` de Apple; el EXIF
  solo datos de cámara/fecha. No existía la caption dentro del archivo.

**Decisión del propietario:** abandonar los metadatos. Los datos del anuncio van
en el **nombre del archivo**: `24.95;50x60;Nike;35A.HEIC`.

**Consecuencias aplicadas**
- `pyexiv2` eliminado de `pyproject.toml` y del pre-commit.
- `metadata.py` solo usa `pathlib` y `re` (stdlib).
- Fixture renombrada y test de integración reescrito.

**Criterio de aceptación:** el test de integración lee precio 24.95, medidas
50x60, marca Nike y modelo 35A desde el nombre del archivo, sin librerías externas.
