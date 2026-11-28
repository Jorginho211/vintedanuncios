# Arquitectura

## Visión general

La publicación corre una vez al día y también se lanza bajo demanda. La respuesta
a favoritos se ejecuta bajo demanda (`vinted reply`) y, con `--schedule`, cada
30-60 minutos con intervalo aleatorio real, nunca entre las 01:00 y las 08:00 de
`TIMEZONE` (plan 029). Abre cada conversación pendiente, ofrece 2 € menos y envía
la plantilla; solo con `--publish` escribe en Vinted (planes 027 y 028). `cli` y `scheduler` leen el entorno una sola vez,
construyen `Settings` y `Mode` y los inyectan. Por defecto trabaja en simulación;
solo con `--publish` escribe en Vinted. `--simulate-send` recorre el formulario
real sin pulsar «Subir».

```
cli / scheduler  ->  Settings + Mode
                          |
                          v
                  features/run_sweep  (composición)
                          |
   run_publish / run_sweep
   valida Data + config
          |
   scan_listings -> publish_listings
          |        -> borrar solo con confirmación
          |
   runtime elige adapters reales o no-op

cli / scheduler -> run_reply -> reply_favorites.scan_favorites(template)
                                -> oferta + mensaje solo con --publish
                               -> lock Selenium + perfil por cuenta
```

## Componentes

| Módulo | Responsabilidad | ¿Toca Selenium/filesystem? |
|---|---|---|
| `shared/settings.py` | Variables de entorno validadas, leídas una vez | No |
| `shared/config.py` | `config.json`, descripción y validación de árboles de datos | Solo lectura de `Data/` |
| `shared/models.py` | Datos inmutables y `Mode` | No |
| `shared/ports.py` | Contratos: driver, publisher, replier, store, runtime | No |
| `shared/offers.py` | Cálculo del precio de la oferta con `Decimal` | No |
| `shared/pause.py` | Pausas configurables | No |
| `shared/selenium_lock.py` | Lock global cross-process para Selenium | Fichero en `profiles_dir` |
| `shared/logging_conf.py` | Configuración de logs | No |
| `adapters/selectors.py` | Selectores CSS y textos de Vinted | No |
| `adapters/selenium_driver.py` | Driver remoto por cuenta | Sí |
| `adapters/vinted_publisher.py` | Formulario de publicación | Sí |
| `adapters/vinted_replier.py` | Oferta y mensaje en notificaciones de favorito | Sí |
| `adapters/vinted_wait.py` | Esperas, scroll y pestañas compartidas | Sí |
| `adapters/filesystem.py` | Borrado de carpetas | Sí |
| `features/scan_listings/` | Query que resuelve los anuncios del árbol | No |
| `features/check_session/` | Abre Vinted con un perfil para verificar la sesión a mano | Indirecto |
| `features/publish_listings/` | Command de publicación + simulación | No |
| `features/reply_favorites/` | Command de respuesta de favoritos + simulación | No |
| `features/run_sweep/` | Orquestación de publicación y reply; selección de adapters según `Mode` | Indirecto |
| `scheduler.py` | Cron de publicación y job aleatorio de respuesta de favoritos | No |
| `cli.py` | Composition root de Typer | No |

## Contrato de datos

Caption: `precio;medidas(ancho x largo);marca(opcional);modelo(opcional)`,
contenida en el **nombre del archivo**: `24.95;50x60;Nike;35A.JPG`.
Medidas en cm (`50x60`). `;` siempre separa; se tolera un `;` final. No se valida
el caso "modelo sin marca" porque se acordó que no puede ocurrir. Solo se
aceptan fotos JPEG/PNG/GIF; los `.HEIC`/`.HEIF` se rechazan en el escaneo con un
mensaje que pide convertirlos a JPEG (Vinted los rechaza con un diálogo crítico).
El orden de adjunción se resuelve en el escaneo: las fotos van ordenadas por
nombre y la que contiene la caption se promueve a la primera posición. Así
`Listing.images` es la única fuente de verdad y el publicador y el dry-run
consumen el mismo orden.

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

Talla: `width_cm` es el ancho plano (media vuelta) y `length_cm` el largo.
`shared/sizes.py` aplica tablas deterministas con rangos `[mín, máx)` (plan 025):
pantalones van de W23 a W38 (28,58–48,90 cm, `W × 1,27`) y dan `WXX | ESXX` con
`ES = W + 10`. Tops usan una matriz vintage de 9 × 9 (ancho × largo) de `XXXS` a
`XXXL`: el ancho fija la talla y un largo tres bandas o más más corto la baja una
posición; `XXXS` y `XXXL` son abiertos en los extremos. Fuera de rango,
`SizeError` se añade a `ScanResult.errors` y el anuncio no se publica.
`Listing.size` guarda la talla calculada y el publicador elige la primera opción
del desplegable que la contiene (`W32` o `ES42`); sin opción, error sin publicar.

Descripción: contenido de `Data/description.txt` con `{{TALLA}}` sustituido por
la talla calculada.

Respuesta: `Data/reply_added_favorites.txt` es el mensaje que se envía a cada
favorito pendiente. El precio anterior se lee del placeholder
`XX,XX €` de `[data-testid="offer-price-field--input"]`, se restan `2,00` con
`Decimal` y se escribe como `XX,XX` antes de pulsar
`[data-testid="offer-submit-button"]`. El mensaje se escribe en
`[data-testid="composer--input"]` y se envía con Enter.

Los archivos `config.json` y `description.txt` son obligatorios para
`run_publish` y `run_sweep`: `validate_data_dir()` se ejecuta una sola vez y `cli`
termina con código 1 si falta alguno. `run_reply` valida el árbol de cuentas con
`validate_reply_data_dir()`; sin cuentas avisa y termina con código 0. En
`--dry-run` no exige plantilla; en los modos reales la lee con
`load_reply_template()` y falla si falta o está vacía.

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
| Intervalo del reply | 30-60 min aleatorio real; sin disparos en 01:00-08:00 y, si cae ahí, 08:00 + 0-30 min (no configurable por env; plan 029) |

`load_settings(environ=None)` centraliza defaults y validación. `TZ` es ignorada
por la aplicación y los nombres antiguos de las pausas no se reconocen: el
proyecto aún no está en producción y no se mantiene compatibilidad.

`ActionPacer` (`shared/pause.py`) aplica un retardo aleatorio entre
`SELENIUM_ACTION_DELAY_MIN` y `MAX` después de cada acción del publicador y, en
`vinted reply`, del replier. Su único fin es dar tiempo al DOM y evitar carreras;
no hay lógica de evasión de anti-bot. Con ambos valores a `0` no se duerme.

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
  `run_sweep` es un alias de `run_publish`; `run_reply` sigue disponible como
  comando manual. Todos comparten el mismo runtime.
- **Simulación por composición:** en `Mode.DRY_RUN` el runtime devuelve publishers
  y store de no-op y no crea ningún driver. En `Mode.SIMULATE_SEND` usa el
  publisher real con `submit=False` y store real; si se invoca `vinted reply`,
  usa el replier real con `send=False`: abre y lee, pero no escribe. En
  `Mode.CHECK_SUBMIT` usa el publisher real con `check_submit=True` y store de
  no-op: rellena el formulario, registra el estado de los campos y del botón
  «Subir» y descarta los cambios sin publicar ni borrar carpetas. Solo
  `Mode.PUBLISH` crea un replier con `send=True`. Los handlers no reciben flags
  `dry_run` ni drivers nulos.
- **Sesión perezosa:** el driver se crea solo para cuentas con trabajo. Tras la
  última acción de la cuenta se cierra. `Runtime.release(account)` lo garantiza
  con `try/finally`.
- **Lock global Selenium:** `shared/selenium_lock.py` usa `fcntl.flock` sobre
  `sessions/.selenium.lock` para evitar solapes entre comandos y jobs, incluso en
  procesos distintos. `DRY_RUN` no lo adquiere.
- **Perfil persistente:** el driver pasa `-profile <ruta del contenedor>` en
  `moz:firefoxOptions.args`; geckodriver usa `sessions/<Cuenta>` in situ a través
  del volumen montado. No se usa `options.profile` porque Selenium comprime el
  perfil y geckodriver lo despliega en `/tmp/rust_mozprofile...`, que se borra al
  cerrar. geckodriver elige el puerto de Marionette leyendo `MarionetteActivePort`
  del perfil, así que no hace falta fijar `--marionette-port`. La carpeta se crea
  con permisos `777` para el usuario del contenedor (uid 1000 en
  `docker-compose.yaml`).
- **Rutas de fotos:** `DATA_DIR` es la ruta del host y `SELENIUM_DATA_DIR` la del
  contenedor. El publisher traduce cada foto a `/Data/<Cuenta>/...` antes de
  `send_keys`. `docker-compose.yaml` monta `./Data:/Data:ro` en Selenium y
  `./Data:/Data:rw` en la app (que borra carpetas de anuncio), y fija
  `SE_NODE_SESSION_TIMEOUT=7200`.
- **Despliegue en contenedores (plan 024):** además de `selenium`, el compose
  define el servicio `vinted` con `ENTRYPOINT=vinted`. Arranca con
  `--publish --schedule` por decisión explícita del propietario y comparte
  `./Data`, `./sessions` y `./logs` con el host. Los comandos sueltos se ejecutan
  con `docker compose run --rm vinted <args>`; la imagen instala solo
  dependencias de producción y no incluye las herramientas de desarrollo.
  Dentro de la red de Compose se fuerza `SELENIUM_URL=http://selenium:4444` y
  las rutas `/Data` y `/sessions`; el resto de parámetros se leen de `.env`.
- **Verificación manual de sesión:** `check-session` abre el home con el perfil
  indicado y deja que el propietario compruebe el login por VNC; no hay detección
  automática ni escritura en Vinted.
- Procesamiento **secuencial** de cuentas (una sola sesión activa por vez).
- Pausas configurables por estabilidad, no para evadir controles.
- Un error en un anuncio se registra y no aborta el barrido. En `reply`, un
  precio ilegible, ≤ 2 € o un fallo al escribir se registran por notificación y
  se continúa con la siguiente; no se reintenta una oferta ya aceptada.
- Borrado de la carpeta hoja del anuncio tras confirmación de Vinted (`--publish`)
  o al terminar `--simulate-send`. `FilesystemListingStore.delete()` exige que la
  ruta esté dentro de `DATA_DIR` y tenga exactamente tres niveles: nunca borra
  carpetas de cuenta ni de categoría. Un resultado ambiguo al publicar es error:
  sin borrado y sin reintentos.
- Sin base de datos local: el estado de las conversaciones lo determina Vinted.
- **Dos jobs programados:** publicación diaria a las 16:00 y `respuesta_favoritos`
  con intervalo aleatorio real de 30-60 minutos, ambos con `max_instances=1`,
  `coalesce=True` y lock global de Selenium. `respuesta_favoritos` se reprograma
  tras cada ejecución. Ningún disparo cae en `[01:00, 08:00)` de `TIMEZONE`: si
  el cálculo cae en esa franja, se difiere a las 08:00 más 0-30 minutos. Se aplica
  al disparo inicial y a cada reprogramación (plan 029).
- **CLI por subcomando:** `publish` y `sweep` publican; `reply` ofrece 2 € menos
  y envía la plantilla a favoritos pendientes, pero solo escribe con
  `--publish`. `--schedule` arranca los jobs programados.

## Selectores del formulario real

Validados con volcados de HTML de CuentaA (`/tmp/opencode/vinted_*.html`, plan 016):

| Paso | Selector |
|---|---|
| «Vender ahora» | `a[href="/items/new"]` |
| Fotos | `[data-testid="add-photos-input"]` (varios archivos separados por salto de línea) |
| Título / descripción / precio | `#title`, `#description`, `#price` |
| Categoría | `[data-testid="catalog-select-dropdown-input"]` + `#catalog-search-input`, primera opción |
| Marca | Se conserva la sugerencia de Vinted solo si coincide; si no, `[data-testid="brand-select-dropdown-input"]` + `#brand-search-input`, primera opción. Sin marca en la caption se abre el desplegable y se recorren las opciones `[data-testid="brand-select-dropdown-content"] [role="radio"][id^="brand-"]` con scroll por JavaScript hasta encontrar `Vintage Dressing` (texto normalizado en minúsculas); el buscador no la ofrece |
| Color | `[data-testid="color-select-dropdown-input"]`; primera sugerencia o primer color de la lista |
| Estado | `#condition-2` («Muy bueno») |
| Talla | `input#size` con `data-testid^="category-size-single-grid"` (pantalones terminan en `-input`; tops y cortavientos en `_chips-input`) + contenido terminado en `-content`, opciones `[role="checkbox"]` o `[role="radio"]`; se lee `aria-label` antes que el texto y se verifica con `aria-checked` o el valor del campo tras elegir |
| Envío | `[data-testid="1-package-size--cell"]` («Pequeño»); el radio `#package_type_selector_1` está oculto |
| Subir | `[data-testid="upload-form-save-button"]` |
| Error de subida | `[data-testid="item-upload-critical-error-dialog"]` |

Material y modelo no se cubren: este último no existe en el DOM de Vinted para
las categorías usadas; se concatena al título. El campo de talla se rellena con
la talla calculada y sus selectores se validaron con `--simulate-send`.

## Selectores del reply

| Paso | Selector |
|---|---|
| Ya respondida | `[data-testid="offer-current-price-label"]` o `[data-testid="conversation-message"]` |
| Precio anterior | `[data-testid="offer-price-field--input"]` (atributo `placeholder`) |
| Enviar oferta | `[data-testid="offer-submit-button"]` |
| Mensaje | `[data-testid="composer--input"]` (se envía con Enter) |

Estos selectores se validan a mano con `docs/checklist.md`; no hay E2E
automatizado contra Vinted (plan 028).

## Riesgos conocidos / pendientes

- El flujo de reply detecta notificaciones en `/member/notifications`, filtra
  `a sus favoritos`, abre pestañas y para si la conversación ya tiene mensajes o
  el marcador `offer-current-price-label`; en las pendientes ofrece 2 € menos y
  envía la plantilla solo con `--publish`.
  Verificar la modal y el orden de acciones con `docs/checklist.md`.
- La caption se lee del nombre del archivo con `pathlib.stem`; no se usan metadatos ni librerías externas.
- El perfil de Firefox en `sessions/<Cuenta>/` se comprueba entre ejecuciones con
  `vinted check-session <Cuenta>` (planes 014 y 020). Si Vinted expulsa la sesión
  por seguridad, hay que volver a iniciarla en VNC; el código no detecta el login.
- Si Vinted cambia el DOM, `--simulate-send` es la forma segura de detectarlo
  antes de publicar. Para el botón «Subir», `--check-submit` informa del estado
  previo al clic; la navegación posterior solo se puede comprobar con
  `--publish` autorizado (plan 026).
