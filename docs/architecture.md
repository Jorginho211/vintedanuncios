# Arquitectura

## Visión general

La publicación corre una vez al día y la revisión de favoritos cada 15 minutos
(configurable con `REPLY_CRON`); ambas acciones también se lanzan bajo demanda.
`cli` y `scheduler` leen el entorno una sola vez, construyen `Settings` y `Mode`
y los inyectan. Por defecto trabaja en simulación; solo con `--publish` escribe
en Vinted. `--simulate-send` recorre el formulario real sin pulsar «Subir».

```
cli / scheduler  ->  Settings + Mode
                          |
                          v
                  features/run_sweep  (composición)
                          |
          +------------------+-------------------+
          |                  |                   |
   run_publish          run_reply        runtime elige
   valida Data          valida Data      adapters reales o no-op
   + config/template    + plantilla
   scan_listings        cuentas de Data
          |                  |
   publish_listings     reply_favorites
   -> borrar solo        -> responde una vez
      con confirmación
```

## Componentes

| Módulo | Responsabilidad | ¿Toca Selenium/filesystem? |
|---|---|---|
| `shared/settings.py` | Variables de entorno validadas, leídas una vez | No |
| `shared/config.py` | `config.json`, descripción y plantilla de respuesta | Solo lectura de `Data/` |
| `shared/models.py` | Datos inmutables y `Mode` | No |
| `shared/ports.py` | Contratos: driver, publisher, replier, store, runtime | No |
| `shared/pause.py` | Pausas configurables | No |
| `shared/logging_conf.py` | Configuración de logs | No |
| `adapters/selectors.py` | Selectores CSS y textos de Vinted | No |
| `adapters/selenium_driver.py` | Driver remoto por cuenta | Sí |
| `adapters/vinted_publisher.py` | Formulario de publicación | Sí |
| `adapters/vinted_replier.py` | Avisos de favorito y respuesta | Sí |
| `adapters/vinted_wait.py` | Esperas y relleno de campos compartidos | Sí |
| `adapters/filesystem.py` | Borrado de carpetas | Sí |
| `features/scan_listings/` | Query que resuelve los anuncios del árbol | No |
| `features/check_session/` | Abre Vinted con un perfil para verificar la sesión a mano | Indirecto |
| `features/publish_listings/` | Command de publicación + simulación | No |
| `features/reply_favorites/` | Command de respuesta + simulación | No |
| `features/run_sweep/` | Orquestación de publicar, responder y barrido completo; selección de adapters según `Mode` | Indirecto |
| `scheduler.py` | Dos crons y bloqueo compartido contra solapes | No |
| `cli.py` | Composition root de Typer | No |

## Contrato de datos

Caption: `precio;medidas(ancho x largo);marca(opcional);modelo(opcional)`,
contenida en el **nombre del archivo**: `24.95;50x60;Nike;35A.JPG`.
Medidas en cm (`50x60`). `;` siempre separa; se tolera un `;` final. No se valida
el caso "modelo sin marca" porque se acordó que no puede ocurrir. Solo se
aceptan fotos JPEG/PNG/GIF; los `.HEIC`/`.HEIF` se rechazan en el escaneo con un
mensaje que pide convertirlos a JPEG (Vinted los rechaza con un diálogo crítico).

`Listing` guarda `config_category` (nombre completo de la carpeta, para
`config.json`) y `form_category` (antes del primer `.`, para el formulario).

Cada categoría de `config.json` incluye la clave reservada `size` (`pants` o
`top`), validada al cargar la configuración y excluida de las variantes de
título. Solo `Pantalones Anchos` usa `pants`.

Título: `<Marca> <Modelo> <Titulo>`; `Titulo` se toma de `config.json` con la
categoría completa y `marca.lower()` (o `default`). La marca se usa también en
el campo «Marca»; Vinted no tiene campo de modelo y las medidas no se envían.
Si la caption no incluye marca, el publicador pone `Vintage Dressing` en el
campo «Marca» (incluso si Vinted sugirió otra), pero no la añade al título:
`Caption.brand` sigue siendo `None` y se usa la variante `default`.

Talla: `width_cm` es el ancho plano (media vuelta). `shared/sizes.py` aplica
tablas deterministas por rangos `[mín, máx)`: pantalones dan `WXX | ES XX` con
`ES = W + 10` (34,29–62,23 cm) y el resto da `XXXS` a `8XL` (30–72 cm), con
`XXL`/`XXXL` en lugar de `2XL`/`3XL` para coincidir con Vinted. Fuera de
rango, `SizeError` se añade a `ScanResult.errors` y el anuncio no se publica.
`Listing.size` guarda la talla calculada y el publicador elige la primera opción
del desplegable que la contiene (`W32` o `ES 42`); sin opción, error sin publicar.

Descripción: contenido de `Data/description.txt` con `{{TALLA}}` sustituido por
la talla calculada.

Respuesta: contenido literal de `Data/reply_added_favorites.txt`.

Los tres archivos de configuración (`config.json`, `description.txt` y
`reply_added_favorites.txt`) son obligatorios para `run_publish` y `run_sweep`:
`validate_data_dir()` se ejecuta una sola vez y `cli` termina con código 1 si
falta alguno. `run_reply` solo valida el árbol de cuentas y la plantilla con
`validate_reply_data_dir()` y `load_reply_template()`; sin cuentas avisa y termina
con código 0.

## Variables de entorno

| Variable | Default |
|---|---|
| `DATA_DIR` | `Data` |
| `SELENIUM_DATA_DIR` | `/Data` |
| `PROFILES_DIR` | `sessions` |
| `SELENIUM_PROFILES_DIR` | `/sessions` |
| `SELENIUM_URL` | `http://127.0.0.1:4444` |
| `SELENIUM_WAIT_SECONDS` | `15` |
| `SELENIUM_ACTION_DELAY_MIN` | `1.0` |
| `SELENIUM_ACTION_DELAY_MAX` | `2.0` |
| `PAUSE_BETWEEN_LISTINGS` | `0` |
| `PAUSE_BETWEEN_ACCOUNTS` | `0` |
| `TIMEZONE` | `Europe/Madrid` |
| `REPLY_CRON` | `*/15 * * * *` |

`load_settings(environ=None)` centraliza defaults y validación. `TZ` es ignorada
por la aplicación y los nombres antiguos de las pausas no se reconocen: el
proyecto aún no está en producción y no se mantiene compatibilidad.

`ActionPacer` (`shared/pause.py`) aplica un retardo aleatorio entre
`SELENIUM_ACTION_DELAY_MIN` y `MAX` después de cada acción del publicador y del
replier. Su único fin es dar tiempo al DOM y evitar carreras; no hay lógica de
evasión de anti-bot. Con ambos valores a `0` no se duerme.

Como Vinted puede re-renderizar un nodo durante esas pausas, los helpers de
`adapters/vinted_wait.py` (`click_css`, `click_xpath`, `fill` y
`send_keys_css`) localizan el elemento de nuevo si aparece
`StaleElementReferenceException`.

## Decisiones

- **Command/Query ligero:** cada caso de uso tiene un objeto de entrada y un
  handler. No hay stores separados, bus de eventos ni event sourcing: no hay base
  de datos y la constitución establece que el filesystem es la fuente de verdad.
- **Slices verticales:** `scan_listings`, `publish_listings`, `reply_favorites` y
  `run_sweep` agrupan la lógica por caso de uso; `shared/` aporta los contratos.
  `run_sweep` expone tres orquestadores: `run_publish`, `run_reply` y el barrido
  completo, que comparten el mismo runtime.
- **Simulación por composición:** en `Mode.DRY_RUN` el runtime devuelve publishers
  y store de no-op y no crea ningún driver. En `Mode.SIMULATE_SEND` usa el
  publisher real con `submit=False`, store real y replier simulado. Los handlers
  no reciben flags `dry_run` ni drivers nulos.
- **Sesión perezosa:** el driver se crea solo para cuentas con trabajo. Tras la
  última publicación de la cuenta se cierra; la fase de favoritos abre su propia
  sesión. `Runtime.release(account)` lo garantiza con `try/finally`.
- **Perfil persistente:** el driver pasa `-profile <ruta del contenedor>` en
  `moz:firefoxOptions.args`; geckodriver usa `sessions/<Cuenta>` in situ a través
  del volumen montado. No se usa `options.profile` porque Selenium comprime el
  perfil y geckodriver lo despliega en `/tmp/rust_mozprofile...`, que se borra al
  cerrar. geckodriver elige el puerto de Marionette leyendo `MarionetteActivePort`
  del perfil, así que no hace falta fijar `--marionette-port`. La carpeta se crea
  con permisos `777` para el usuario `seluser` (uid 1200) del contenedor.
- **Rutas de fotos:** `DATA_DIR` es la ruta del host y `SELENIUM_DATA_DIR` la del
  contenedor. El publisher traduce cada foto a `/Data/<Cuenta>/...` antes de
  `send_keys`. `docker-compose.yaml` monta `./Data:/Data:ro` y fija
  `SE_NODE_SESSION_TIMEOUT=1800`.
- **Verificación manual de sesión:** `check-session` abre el home con el perfil
  indicado y deja que el propietario compruebe el login por VNC; no hay detección
  automática ni escritura en Vinted.
- Procesamiento **secuencial** de cuentas (una sola sesión activa por vez).
- Pausas configurables por estabilidad, no para evadir controles.
- Un error en un anuncio se registra y no aborta el barrido.
- Borrado de la carpeta hoja del anuncio tras confirmación de Vinted (`--publish`)
  o al terminar `--simulate-send`. `FilesystemListingStore.delete()` exige que la
  ruta esté dentro de `DATA_DIR` y tenga exactamente tres niveles: nunca borra
  carpetas de cuenta ni de categoría. Un resultado ambiguo al publicar es error:
  sin borrado y sin reintentos.
- Sin base de datos local: el estado de las conversaciones lo determina Vinted.
- **Dos jobs, un perfil a la vez:** publicación diaria y favoritos comparten un
  `Lock`; cada job tiene `max_instances=1` y `coalesce=True`. Un cron inválido en
  `REPLY_CRON` se rechaza al arrancar con `SettingsError`.
- **CLI por subcomando:** `publish` y `reply` son acciones puntuales; `sweep` (o
  `vinted` sin subcomando) mantiene el barrido completo y `--schedule` arranca los
  dos jobs programados.

## Selectores del formulario real

Validados con volcados de HTML de CuentaA (`/tmp/opencode/vinted_*.html`, plan 016):

| Paso | Selector |
|---|---|
| «Vender ahora» | `a[href="/items/new"]` |
| Fotos | `[data-testid="add-photos-input"]` (varios archivos separados por salto de línea) |
| Título / descripción / precio | `#title`, `#description`, `#price` |
| Categoría | `[data-testid="catalog-select-dropdown-input"]` + `#catalog-search-input`, primera opción |
| Marca | Se conserva la sugerencia de Vinted solo si coincide; si no, `[data-testid="brand-select-dropdown-input"]` + `#brand-search-input`, primera opción. Sin marca en la caption se busca siempre `Vintage Dressing` |
| Color | `[data-testid="color-select-dropdown-input"]`; primera sugerencia o primer color de la lista |
| Estado | `#condition-2` («Muy bueno») |
| Talla | `[data-testid="category-size-single-grid-input"]` + opciones `[data-testid="category-size-single-grid-content"] [role="checkbox"]` (Vinted ofrece pares como `W34 | ES 44`) |
| Envío | `[data-testid="1-package-size--cell"]` («Pequeño»); el radio `#package_type_selector_1` está oculto |
| Subir | `[data-testid="upload-form-save-button"]` |
| Error de subida | `[data-testid="item-upload-critical-error-dialog"]` |

Material y modelo no se cubren: este último no existe en el DOM de Vinted para
las categorías usadas; se concatena al título. El campo de talla se rellena con
la talla calculada y sus selectores se validaron con `--simulate-send`.

## Riesgos conocidos / pendientes

- Los selectores de favoritos siguen siendo provisionales: validar la ubicación
  de la alerta «ha marcado como favorito tu artículo» con `docs/checklist.md`.
- La caption se lee del nombre del archivo con `pathlib.stem`; no se usan metadatos ni librerías externas.
- El perfil de Firefox en `sessions/<Cuenta>/` se comprueba entre ejecuciones con
  `vinted check-session <Cuenta>` (planes 014 y 020). Si Vinted expulsa la sesión
  por seguridad, hay que volver a iniciarla en VNC; el código no detecta el login.
- Si Vinted cambia el DOM, `--simulate-send` es la forma segura de detectarlo
  antes de publicar.
