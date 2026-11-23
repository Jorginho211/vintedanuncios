# Arquitectura

## Visión general

La publicación corre una vez al día y la revisión de favoritos cada 15 minutos
(configurable con `REPLY_CRON`); ambas acciones también se lanzan bajo demanda.
`cli` y `scheduler` leen el entorno una sola vez, construyen `Settings` y `Mode`
y los inyectan. Por defecto trabaja en simulación; solo con `--publish` interactúa
con Vinted.

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
contenida en el **nombre del archivo**: `24.95;50x60;Nike;35A.HEIC`.
Medidas en cm (`50x60`). `;` siempre separa; se tolera un `;` final. No se valida
el caso "modelo sin marca" porque se acordó que no puede ocurrir.

Título: categoría (nombre de carpeta exacto, los puntos son literales) +
`marca.lower()`; si la clave no existe, `default`.

Descripción: contenido literal de `Data/description.txt`. Si el texto incluye
`{{TALLA}}`, se deja tal cual hasta una iteración futura.

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
| `PROFILES_DIR` | `sessions` |
| `SELENIUM_URL` | `http://127.0.0.1:4444` |
| `SELENIUM_WAIT_SECONDS` | `15` |
| `PAUSE_BETWEEN_LISTINGS` | `0` |
| `PAUSE_BETWEEN_ACCOUNTS` | `0` |
| `TIMEZONE` | `Europe/Madrid` |
| `REPLY_CRON` | `*/15 * * * *` |

`load_settings(environ=None)` centraliza defaults y validación. `TZ` es ignorada
por la aplicación y los nombres antiguos de las pausas no se reconocen: el
proyecto aún no está en producción y no se mantiene compatibilidad.

## Decisiones

- **Command/Query ligero:** cada caso de uso tiene un objeto de entrada y un
  handler. No hay stores separados, bus de eventos ni event sourcing: no hay base
  de datos y la constitución establece que el filesystem es la fuente de verdad.
- **Slices verticales:** `scan_listings`, `publish_listings`, `reply_favorites` y
  `run_sweep` agrupan la lógica por caso de uso; `shared/` aporta los contratos.
  `run_sweep` expone tres orquestadores: `run_publish`, `run_reply` y el barrido
  completo, que comparten el mismo runtime.
- **Simulación por composición:** en `Mode.DRY_RUN` el runtime devuelve publishers
  y store de no-op y no crea ningún driver. Los handlers no reciben flags
  `dry_run` ni drivers nulos.
- **Verificación manual de sesión:** `check-session` abre el home con el perfil
  indicado y deja que el propietario compruebe el login por VNC; no hay detección
  automática ni escritura en Vinted.
- Procesamiento **secuencial** de cuentas (una sola sesión activa por vez).
- Pausas configurables por estabilidad, no para evadir controles.
- Un error en un anuncio se registra y no aborta el barrido.
- Borrado real de la carpeta **solo** tras confirmación de Vinted y con `--publish`.
- Sin base de datos local: el estado de las conversaciones lo determina Vinted.
- **Dos jobs, un perfil a la vez:** publicación diaria y favoritos comparten un
  `Lock`; cada job tiene `max_instances=1` y `coalesce=True`. Un cron inválido en
  `REPLY_CRON` se rechaza al arrancar con `SettingsError`.
- **CLI por subcomando:** `publish` y `reply` son acciones puntuales; `sweep` (o
  `vinted` sin subcomando) mantiene el barrido completo y `--schedule` arranca los
  dos jobs programados.

## Riesgos conocidos / pendientes

- Los selectores de `adapters/selectors.py` son provisionales: validar contra la web real.
- La ubicación de la alerta de favorito está pendiente de confirmar.
- La caption se lee del nombre del archivo con `pathlib.stem`; no se usan metadatos ni librerías externas.
- El perfil de Firefox en `sessions/<Cuenta>/` debe verificarse entre ejecuciones
  con `vinted check-session <Cuenta>` (plan 014).
- Destino del campo `modelo` en el formulario de Vinted: pendiente.
