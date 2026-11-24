# Plan 018 — Talla determinista por categoría y medidas

> **Nota:** las tablas de tallas de este plan quedaron sustituidas por el plan
> 025 (pantalones W23–W38 con `WXX | ESXX` y tops vintage ancho × largo).

**Estado:** implementado y validado con `--simulate-send` en CuentaA para las dos
ramas (pantalón `42x95` → `W34 | ES 44` y sudadera `51x70` → `XXL`). Los
selectores iniciales eran incorrectos; se corrigieron a
`category-size-single-grid-input` y `category-size-single-grid-content [role="checkbox"]`.
Vinted nombra las tallas superiores `XXL`/`XXXL`, no `2XL`/`3XL`.

## Objetivo

Calcular la talla de cada anuncio de forma determinista a partir de `width_cm` y
de la categoría configurada en `Data/config.json`, resolver el placeholder
`{{TALLA}}` en la descripción y seleccionar la talla en el formulario de Vinted.

Cierra el plan 010.

## Decisiones acordadas con el propietario

- `Data/config.json` lleva una clave reservada `size` por categoría: `pants` o
  `top`. Solo `Pantalones Anchos` es `pants`; el resto son `top`.
- `width_cm` es el ancho plano de la prenda (media vuelta de cintura/pecho).
- Pantalones: tabla por rangos de ancho plano con salida `WXX | ES XX` y
  equivalencia `ES = W + 10`. Superiores: `XXXS` a `8XL`.
- Medida fuera de tabla: error de escaneo; el anuncio no se publica.
- En Vinted se busca una opción que contenga `W32` o `ES 42` (según la talla
  calculada) y se elige la primera que aparece en el DOM. Si no hay opción,
  error controlado sin publicación.

## Cambios previstos

1. `shared/sizes.py`: lógica pura con las tablas, `SizeError` y normalización de
   opciones para Vinted.
2. `shared/config.py`: validar la clave `size` y excluirla de las variantes de
   título.
3. `shared/models.py`: `Listing.size`.
4. `features/scan_listings/handler.py`: calcular la talla, sustituir
   `{{TALLA}}` y registrar errores de talla.
5. `adapters/selectors.py` y `adapters/vinted_publisher.py`: selector del
   desplegable de talla y paso `_choose_size()` tras la categoría.
6. `Data/config.json.example`, `Data/config.json`, documentación y checklist.
7. Tests unitarios de tablas, límites, configuración, escaneo y publicador.

## Verificación

- `poetry run ruff check .`, `poetry run mypy src tests`, `poetry run pytest`.
- `poetry run vinted --dry-run`: descripción con la talla resuelta.
- `poetry run vinted --simulate-send` con un anuncio de cada rama: comprobar el
  campo «Talla» (`W34 | ES 44` verificado en el valor del desplegable; `XXL`
  seleccionado sin error de opción), que no se pulsa «Subir» y que solo se
  borran las carpetas hoja. Sin `--publish`. `Data/` se restauró de la copia.
- `pytest` en verde: se actualizaron el test de plantillas y el de defaults de
  `action_delay_*` a los nombres y valores vigentes, junto con su documentación.
