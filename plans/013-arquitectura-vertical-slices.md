# Plan 013 — Arquitectura: slices verticales y Command/Query ligero

**Estado:** completado.

**Objetivo:** eliminar duplicidades y acoplamientos de la arquitectura actual mediante
configuración de entorno centralizada, puertos explícitos y organización por caso de uso,
sin sobreingeniería (sin stores separados, eventos ni bus de mensajes).

**Decisiones acordadas con el propietario**
1. CQRS en forma ligera: un objeto Command/Query y un handler por caso de uso.
2. Estructura de carpetas: `features/` (slices), `shared/` (dominio y contratos),
   `adapters/` (Selenium y filesystem).
3. `settings.py` separado de `config.py`: entorno/runtime frente a datos de `Data/`.
4. Variables de entorno en inglés, alineadas con los campos de `Settings`.
5. `TZ` se renombra a `TIMEZONE` (sin fallback).
6. Sin compatibilidad hacia atrás ni salvaguardas para nombres antiguos: el proyecto
   aún no está en producción.

## Contrato de entorno final

| Variable | Default | Campo `Settings` |
|---|---|---|
| `DATA_DIR` | `Data` | `data_dir` |
| `PROFILES_DIR` | `sessions` | `profiles_dir` |
| `SELENIUM_URL` | `http://127.0.0.1:4444` | `selenium_url` |
| `SELENIUM_WAIT_SECONDS` | `15` | `wait_seconds` |
| `PAUSE_BETWEEN_LISTINGS` | `0` | `pause_between_listings` |
| `PAUSE_BETWEEN_ACCOUNTS` | `0` | `pause_between_accounts` |
| `TIMEZONE` | `Europe/Madrid` | `timezone` |

`TZ` queda ignorada por la aplicación (documentado en `.env.example` y `README.md`).
Los nombres antiguos de las pausas también quedan ignorados: no hay detección ni avisos.

## Cambios por fase

### Fase 1 — Configuración centralizada
- `shared/settings.py` con `Settings` y `load_settings(environ=None)`, validación de
  números, URL y zona horaria; se lee el entorno una sola vez en `cli`.
- `cli` inyecta `Settings`; `runner`, `browser` y `scheduler` dejan de usar `os.getenv`.
- `.env.example`, `README.md` y `CONSTITUTION.md` actualizados; tests de settings.

### Fase 2 — Puertos y modo explícito
- `Mode.DRY_RUN / Mode.PUBLISH` en `shared/models.py`, calculado una sola vez en `cli`.
- `shared/ports.py`: `DriverPort`, `ElementPort`, `DriverFactory`, `ListingPublisher`,
  `FavoriteReplier`, `ListingStore`, `Runtime`.
- Adapters de Selenium y filesystem implementan esos puertos; desaparecen los flags
  `dry_run` y los `driver: WebDriver | None` de los handlers.

### Fase 3 — Slices verticales
- `features/scan_listings/` (Query), `features/publish_listings/` (Command),
  `features/reply_favorites/` (Command), `features/run_sweep/` (composición).
- Implementaciones de simulación (`DryRunListingPublisher`, `DryRunFavoriteReplier`,
  `NoOpListingStore`) seleccionadas por el runtime según `Mode`.
- Tests espejo por slice; cobertura y documentación actualizadas.

## Criterios de aceptación
- `poetry run ruff check .`, `poetry run mypy src tests`, `poetry run pytest` en verde.
- `poetry run vinted --dry-run` sin Docker: no crea navegador, no borra carpetas.
- Con `--publish`: se crea un driver por cuenta y la carpeta se borra solo tras
  confirmación, y solo en modo publicación.
- Sin archivos obligatorios: error con código de salida 1, antes de escanear.
- `CONSTITUTION.md` y `docs/` sincronizados con la estructura final.

## Resultado

- `ruff check`, `ruff format`, `mypy src tests` y `pytest` en verde: 47 tests,
  97 % de cobertura sobre la lógica pura incluida en la medición.
- `poetry run vinted --dry-run` termina sin crear drivers ni borrar carpetas.
- Sin cambios en `sessions/`, sin ejecución de `--publish` y sin E2E contra Vinted.

## Prohibiciones respetadas
- No ejecutar `--publish` contra Vinted.
- No tocar `sessions/` (solo `sessions/.gitkeep` está versionado).
- No automatizar E2E contra Vinted.
