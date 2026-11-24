# Plan 021 — Seleccionar la marca por defecto recorriendo el listado

**Estado:** completado. Verificado con ruff, mypy y pytest en verde y con
`--simulate-send` el 2026-11-24: la marca por defecto se seleccionó recorriendo
el desplegable y el campo quedó con `Vintage Dressing`; la simulación terminó
sin pulsar «Subir» y se restauró la copia de `Data/`. Antes de la ejecución
correcta hubo dos fallos transitorios del formulario (timeout en marca y
«Vinted no ofreció colores»), no reproducibles en la repetición.

## Objetivo

`Vintage Dressing` no se puede seleccionar con `#brand-search-input`: en el
desplegable de marcas de Vinted solo aparece al desplazarse por la lista
completa. El publicador debe encontrarla y pulsarla sin depender del buscador.

## Decisiones acordadas con el propietario

- El fallback por scroll se aplica **solo** a `DEFAULT_BRAND`. Las marcas que
  vienen en la caption siguen usando el buscador y la primera opción, como hasta
  ahora; no se cambia la selección de categoría.
- Para la marca por defecto **no se escribe en el buscador**: se abre el
  desplegable y se recorre el listado.
- La comparación del texto de las opciones se hace en minúsculas y normalizada
  (sin espacios ni caracteres no alfanuméricos), reutilizando
  `_normalized_brand()`.
- Si Vinted ya sugiere la marca por defecto, se conserva la sugerencia y no se
  abre el desplegable.
- Sin coincidencia al final del listado: error en español, sin publicar y sin
  reintentos automáticos.

## Cambios previstos

1. `adapters/vinted_wait.py`: helper para avanzar un bloque el ancestro con
   scroll que contiene un selector, devolviendo si `scrollTop` cambió. Misma
   técnica de `click_js()` (`execute_script` con `cast(WebDriver, driver)`), sin
   ampliar `DriverPort`.
2. `adapters/vinted_publisher.py`: en `_ensure_brand()`, bifurcar entre el
   buscador habitual y el nuevo `_choose_default_brand_by_scroll()`; tope de
   pasos, corte por falta de avance, logging en español y pausas con `_pace()`.
3. Tests unitarios con fakes: enrutado por marca, normalización del texto,
   coincidencia tras varios scrolls, agotamiento y estancamiento del listado,
   y ausencia de regresión en categoría.
4. `CONSTITUTION.md`, `docs/architecture.md` y `docs/checklist.md`: documentar
   el mecanismo de selección de la marca por defecto. El plan 019 queda cerrado.

## Verificación

- `poetry run ruff check .`, `poetry run ruff format .`,
  `poetry run mypy src tests`, `poetry run pytest`.
- `poetry run vinted --dry-run` sin cambios de comportamiento.
- `poetry run vinted --simulate-send` con VNC y un anuncio sin marca: comprobar
  que el campo «Marca» queda con `Vintage Dressing` tras recorrer el listado.
  Nunca `--publish` sin autorización explícita.
