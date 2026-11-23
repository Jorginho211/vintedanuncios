# Plan 016 — Corrección del publicador y modo `--simulate-send`

**Estado:** completado (validado el 2026-11-23 con CuentaA).

**Objetivo:** arreglar el flujo de publicación real (categorías, fotos, selectores y
ciclo de vida de la sesión) y añadir un modo de prueba que recorra el formulario
completo en Vinted sin pulsar «Subir».

## Decisiones acordadas con el propietario

1. El árbol es `Data/<Cuenta>/<Categoría>/<Anuncio>/` con fotos **en JPEG**. Una
   de las fotos lleva la caption `precio;medidas;marca;modelo` en el nombre.
   Vinted rechaza `.HEIC` con `item-upload-critical-error-dialog`; el publicador
   no convierte imágenes: las sube tal cual (el propietario las deja en JPEG).
2. Categoría para Vinted: nombre de la carpeta antes del primer `.`.
   Categoría para `config.json`: nombre **completo** de la carpeta (clave del
   título). Ambas se guardan por separado en `Listing`.
3. Título: `<Marca> <Modelo> <Titulo>`, donde `Titulo` sale de `config.json`
   usando la clave completa + variante de marca (si existe). La marca se usa
   también en el campo «Marca» del formulario; el modelo **no tiene campo** en
   Vinted y solo va en el título. Descripción: literal de `Data/description.txt`.
   Medidas: no se envían.
4. `docker-compose.yaml` monta `./Data:/Data:ro`. Las rutas de las fotos se
   traducen al contenedor antes de `send_keys` (`/Data/...`).
5. El driver se crea de forma perezosa solo para cuentas con anuncios y se cierra
   en cuanto termina la última publicación de esa cuenta. En el barrido completo
   la sesión de publicación no queda abierta durante la fase de favoritos.
6. `SE_NODE_SESSION_TIMEOUT=1800` en el grid (antes 300 s).
7. Si la sesión expira y no se sabe si Vinted publicó: error, carpeta intacta y
   revisión manual. Sin reintentos automáticos.
8. Modos mutuamente exclusivos:
   - `--dry-run` (por defecto): sin navegador, sin borrado.
   - `--simulate-send`: navegador real, rellena todo, **no pulsa Subir**, vuelve
     atrás y borra solo las carpetas de los anuncios (nunca las de cuenta ni
     categoría). Las respuestas a favoritos se simulan.
   - `--publish`: navegador real, pulsa Subir y borra tras confirmación real.
9. Flujo del formulario: «Vender ahora» → fotos → título → descripción →
   categoría (buscador, primera opción) → marca (se conserva la sugerencia de
   Vinted; si no hay, buscador y primera opción; no hay campo de modelo) → color (primera sugerencia automática de las fotos; si
   no hay sugerencias, primer color de «Todos los colores») → estado «Muy
   bueno» → talla y material sin cubrir → envío «Pequeño» (primera opción).
10. En `--simulate-send` se vuelve atrás sin pulsar Subir; si Vinted muestra un
    diálogo de cambios sin guardar, se confirma el descarte.

## Fases

### Fase 1 — Inspección (hecha)
- Volcados en `/tmp/opencode/vinted_*.html` (fuera del repo).
- Selectores reales documentados en `docs/architecture.md`: `a[href="/items/new"]`,
  `[data-testid="add-photos-input"]`, `#title`, `#description`, `#price`,
  `[data-testid="catalog-select-dropdown-input"]` + `#catalog-search-input`,
  `[data-testid="brand-select-dropdown-input"]` + `#brand-search-input` (solo si
  Vinted no sugiere ya la marca), color por `aria-labelledby`, `#condition-2`,
  `[data-testid="1-package-size--cell"]` (el radio `#package_type_selector_1`
  está oculto) y `[data-testid="upload-form-save-button"]`.
- Confirmado: no existe campo «Modelo»; el modelo va en el título.

### Fase 2 — Datos y configuración
- `Listing`: `config_category` + `form_category`.
- `Settings`: ruta del árbol dentro del contenedor (`SELENIUM_DATA_DIR`, por
  defecto `/Data`).
- Traducción de rutas en `adapters/`.

### Fase 3 — Selenium
- Selectores y publisher con el flujo real y `submit` configurable.
- Runtime con sesión perezosa por cuenta y cierre al terminar la cuenta.
- `Mode.SIMULATE_SEND` y flag de CLI.

### Fase 4 — Seguridad y pruebas
- `FilesystemListingStore` con guarda de ruta: solo se borra la carpeta hoja del
  anuncio; nunca la de cuenta ni la de categoría.
- Tests unitarios de categoría, rutas, modos y borrado seguro. Sin E2E contra
  Vinted.
- Actualizar `CONSTITUTION.md`, `README.md`, `.env.example`,
  `docs/architecture.md` y `docs/checklist.md`.

## Criterios de aceptación

- `ruff check`, `ruff format --check`, `mypy src tests` y `pytest` en verde.
- `--dry-run` sigue sin crear drivers ni borrar carpetas.
- `--simulate-send` llega hasta justo antes de Subir, no lo pulsa, vuelve atrás
  y borra únicamente `Data/<Cuenta>/<Categoría>/<Anuncio>/`.
- `--publish` no se ejecuta en esta iteración; el propietario lo hará a mano con
  un anuncio nuevo.
- Sin secretos ni perfiles versionados.

## Validación final (2026-11-23)

- `ruff check`, `ruff format --check`, `mypy src tests` y `pytest` en verde
  (87 pruebas).
- `--simulate-send` con CuentaA: los dos anuncios llegaron a
  «simulado (sin pulsar Subir)»; se volvió atrás descartando cambios y se
  borraron solo `Data/CuentaA/<Categoría>/anuncio1/`. Las carpetas de cuenta y
  categoría siguen existiendo; el grid no dejó sesiones activas.
- `--dry-run` posterior no encuentra anuncios pendientes, como corresponde tras
  la simulación. Copia de los 18 archivos originales en
  `/tmp/opencode/DataBackupCuentaA` (fuera del repo).
- No se pulsó «Subir» ni se ejecutó `--publish`.
