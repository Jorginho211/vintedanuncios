# Plan 015 — Barridos independientes de publicación y favoritos

**Estado:** parcialmente retirado (plan 023). Se conservan `vinted publish` y
`vinted reply` como acciones manuales, pero `sweep` ya no responde favoritos y
el scheduler registra sólo el job de publicación, sin bloqueo compartido. El
resto del documento describe la decisión original.

**Objetivo:** separar la publicación diaria de anuncios de la comprobación periódica
de favoritos, para poder responder antes sin publicar de nuevo. Las cuentas se
siguen resolviendo desde las carpetas de `Data/<Cuenta>/` y cada una abre su perfil
de `sessions/<Cuenta>/`.

**Decisiones acordadas con el propietario**
1. CLI: subcomandos `vinted publish` y `vinted reply`. Se conserva `vinted` sin
   subcomando y `vinted sweep` como barrido completo (publicar + responder).
2. Scheduler: dos jobs en el mismo proceso (`publicacion_diaria` a las 16:00 y
   `respuesta_favoritos` según `REPLY_CRON`), con `max_instances=1`, `coalesce=True`
   y un bloqueo compartido para no abrir dos veces el mismo perfil Firefox.
3. Frecuencia de favoritos: `REPLY_CRON`, por defecto `*/15 * * * *`, en la zona
   `TIMEZONE` (por defecto `Europe/Madrid`).
4. El comando `reply` exige solo que exista `Data/`, con al menos una carpeta de
   cuenta, y la plantilla `reply_added_favorites.txt`. Sin cuentas: aviso en español
   y salida limpia (código 0). `config.json` y `description.txt` siguen siendo
   obligatorios para `publish` y `sweep`.
5. No se añade estado local: Vinted determina qué conversación ya fue respondida
   (Constitución §2.4). Se reutiliza `SeleniumRuntime` y `reply_favorites`.

## Cambios por fase

### Fase 1 — Orquestación y configuración
- `features/run_sweep/handler.py`: extraer `run_publish` y añadir `run_reply`,
  manteniendo `run_sweep` como agregador con un único runtime.
- `shared/config.py`: validación ligera del árbol `Data` para el reply; la plantilla
  se sigue validando con `load_reply_template`.
- `shared/settings.py`: nueva variable `REPLY_CRON` (no vacía).
- `scheduler.py`: dos jobs con trigger propio y bloqueo compartido; cron inválido →
  `SettingsError` en español.

### Fase 2 — CLI
- `cli.py`: subcomandos `publish`, `reply` y `sweep`; `--schedule` sigue disponible
  en el barrido completo y arranca los dos jobs. `check-session` intacto.

### Fase 3 — Pruebas y documentación
- Tests unitarios de `run_publish`, `run_reply`, CLI y scheduler con dobles; sin
  Selenium, sin red y sin `--publish`.
- Actualizar `CONSTITUTION.md`, `README.md`, `.env.example`, `docs/architecture.md`,
  `docs/testing.md` y `docs/checklist.md`.

## Criterios de aceptación
- `ruff check`, `ruff format --check`, `mypy src tests` y `pytest` en verde.
- `vinted --dry-run` y `vinted sweep --dry-run` conservan el barrido completo.
- `vinted publish --dry-run` no responde favoritos; `vinted reply --dry-run` no
  escanea ni publica y funciona sin `config.json`/`description.txt`.
- `vinted reply --dry-run` con `Data/` vacío avisa y termina con código 0; sin
  plantilla termina con código 1.
- `--schedule` registra los dos jobs con el bloqueo compartido.
- Sin cambios en `sessions/`, sin ejecución de `--publish` y sin E2E contra Vinted.

## Resultado

- `ruff check`, `ruff format --check`, `mypy src tests` y `pytest` en verde:
  73 tests, 98 % de cobertura sobre la lógica pura medida.
- `vinted --help` muestra `publish`, `reply`, `sweep` y `check-session`; los
  subcomandos `publish` y `reply` aceptan `--publish`/`--dry-run`.
- `run_publish` publica sin responder; `run_reply` recorre las carpetas de cuenta
  y funciona sin `config.json`/`description.txt`.
- `--schedule` registra `publicacion_diaria` y `respuesta_favoritos` con el bloqueo
  compartido; un `REPLY_CRON` inválido se rechaza al arrancar.
- Sin cambios en `sessions/`, sin `--publish` y sin prueba E2E contra Vinted.
