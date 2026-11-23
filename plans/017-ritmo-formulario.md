# Plan 017 — Pausas configurables en el flujo Selenium

**Estado:** completado (validado el 2026-11-23 con CuentaA).

**Objetivo:** dar tiempo al DOM de Vinted para reaccionar entre acciones del
formulario y de la revisión de favoritos, reduciendo carreras y haciendo el ritmo
reproducible mediante configuración.

## Alcance y límites

- Solo retardos explícitos entre acciones de Selenium.
- **No** se añaden trucos para evadir controles anti-bot: ni rotación de
  user-agent/huellas, ni elusión de CAPTCHA, ni imitación de eventos de ratón
  humanos. La finalidad es fiabilidad, no pasar desapercibido.
- No afecta a `--dry-run` (ese modo no crea drivers).
- Se aplica por igual a `--simulate-send` y a `--publish`, y también a la fase
  real de favoritos de `--publish`/barrido.

## Decisiones acordadas con el propietario

1. Pausa con jitter uniforme entre `0,5` y `1,5` segundos por acción.
2. Se aplica a **todo el flujo Selenium**: navegación, subida de fotos, campos
   de texto, desplegables, clics, envío y respuestas a favoritos.
3. Los límites se configuran con `SELENIUM_ACTION_DELAY_MIN` y
   `SELENIUM_ACTION_DELAY_MAX` (segundos, decimals permitidos).
4. Valores a `0` desactivan la pausa; el rango se valida (min <= max).
5. El generador aleatorio y `sleep` son inyectables para poder probarlo sin
   esperas reales.

## Fases

### Fase 1 — Configuración
- `Settings`: nuevos campos `action_delay_min` / `action_delay_max`.
- `load_settings`: defaults `0.5` / `1.5`, validación de rango.

### Fase 2 — Pacer
- `shared/pause.py`: `ActionPacer` con `pause()` usando `random.uniform` y
  `time.sleep` inyectables.
- Tests unitarios del pacer y de la configuración.

### Fase 3 — Integración
- `VintedListingPublisher`: pausa tras navegación, fotos, cada campo, cada
  desplegable, estado, envío, Subir y volver atrás.
- `VintedFavoriteReplier`: pausa tras navegación, apertura de aviso y envío.
- `adapters/vinted_wait.py`: `retry_on_stale` y helpers `click_css`,
  `click_xpath`, `fill` y `send_keys_css` que vuelven a localizar el nodo si
  Vinted lo sustituye durante una pausa (apareció un
  `StaleElementReferenceException` al validar).

### Fase 4 — Documentación y validación
- Actualizar `.env.example`, `README.md`, `docs/architecture.md` y
  `CONSTITUTION.md` si procede.
- `ruff`, `mypy`, `pytest` en verde.
- Restaurar un anuncio desde `/tmp/opencode/DataBackupCuentaA` y ejecutar
  `--simulate-send` para comprobar que el ritmo no rompe ningún selector.
  No ejecutar `--publish`.

## Criterios de aceptación

- Las pausas se pueden subir, bajar o desactivar desde el entorno.
- Sin pausas cuando el modo es `--dry-run`.
- `--simulate-send` sigue sin pulsar «Subir» y borra solo carpetas hoja.
- No se introducen mecanismos de evasión de anti-bot.

## Validación final (2026-11-23)

- `ruff check`, `ruff format --check`, `mypy src tests` y `pytest` en verde
  (95 pruebas).
- Restaurado `anuncio1` de `Pantalones Anchos` desde
  `/tmp/opencode/DataBackupCuentaA` y ejecutado `--simulate-send` con los
  valores por defecto (0,5–1,5 s): terminó en
  «simulado (sin pulsar Subir)» en ~83 s, borró solo la carpeta hoja y no dejó
  sesiones abiertas en el grid.
- `--dry-run` posterior no encuentra anuncios pendientes.
- No se ejecutó `--publish`.
