# Plan 019 — Marca por defecto «Vintage Dressing»

**Estado:** implementado. Verificado con ruff, mypy y pytest en verde.
Pendiente de comprobar en `--simulate-send` que Vinted ofrece `Vintage Dressing`
en el buscador de marcas.

## Objetivo

Cuando la caption del anuncio no incluye marca, rellenar el campo «Marca» del
formulario de Vinted con `Vintage Dressing`, sin que esa marca aparezca en el
título del anuncio.

## Decisiones acordadas con el propietario

- El valor `Vintage Dressing` es una constante en código, dentro del publicador;
  no se añade ninguna clave a `Data/config.json`.
- El fallback se aplica solo al campo «Marca» del formulario. `Caption.brand`
  sigue siendo `None` y el título continúa resolviéndose con la variante
  `default` de `config.json`: `<Modelo> <Titulo>`, sin prefijo de marca.
- Si Vinted sugiere otra marca desde las fotos, se sobrescribe con
  `Vintage Dressing`. Si ya sugiere `Vintage Dressing`, se conserva.

## Cambios previstos

1. `adapters/vinted_publisher.py`: constante `DEFAULT_BRAND` y llamada
   incondicional a `_ensure_brand(listing.caption.brand or DEFAULT_BRAND)`.
2. Tests del publicador para el fallback con y sin marca en la caption, y test
   de escaneo que blinde que el título no incluye `Vintage Dressing`.
3. `CONSTITUTION.md`, `docs/architecture.md` y `README.md`: documentar que el
   fallback es exclusivo del campo «Marca».

## Verificación

- `poetry run ruff check .`, `poetry run ruff format .`,
  `poetry run mypy src tests`, `poetry run pytest`.
- `poetry run vinted --dry-run` y, si se dispone de Selenium,
  `poetry run vinted --simulate-send` comprobando que el campo «Marca» contiene
  `Vintage Dressing` en un anuncio sin marca y que el título no lo incluye.
  Nunca `--publish` sin autorización explícita.
- Riesgo: `_choose_from_search` falla si Vinted no ofrece `Vintage Dressing`
  entre las opciones del buscador de marcas; verificar en la simulación.
