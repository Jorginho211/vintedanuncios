# Plan 022 — Orden de adjunción de fotos

## Estado

Completado.

## Objetivo

Que las fotos de un anuncio se adjunten ordenadas por nombre, con la foto que
lleva la caption (`precio;medidas;marca;modelo`) siempre en la primera posición.

## Decisiones consultadas

- El contrato de la caption **no cambia**: se mantiene `precio;medidas;marca;modelo`.
- No se contemplan dos fotos con caption en la misma carpeta; si ocurriera, se
  toma la primera por nombre como criterio determinista.
- La reorderización se aplica en el escaneo, no en el publicador, para que
  `Listing.images` sea la única fuente de verdad (dry-run incluido).

## Cambios

1. `features/scan_listings/query.py`: nueva función
   `caption_and_image_from_images()` que devuelve `(Caption, Path)` de la primera
   imagen con caption válida. `caption_from_images()` se retira: ya no tenía
   llamadores y su función la cubre la nueva API.
2. `features/scan_listings/handler.py`: ordenar por nombre, promover la foto de
   la caption a la posición 0 y conservar el resto en orden alfabético.
3. Tests unitarios del scanner: foto con caption que alfabéticamente va después
   de otras fotos y caso con la caption ya en primera posición.
4. Documentación: `CONSTITUTION.md`, `docs/architecture.md` y
   `docs/checklist.md`.

## Verificación

- `poetry run ruff check .` y `poetry run ruff format --check .`
- `poetry run mypy src tests`
- `poetry run pytest`
- Sin `--publish` y sin pruebas E2E contra Vinted.
