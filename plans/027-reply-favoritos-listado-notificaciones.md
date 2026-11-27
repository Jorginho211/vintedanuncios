# Plan 027 — Listado automático de notificaciones de favoritos

**Estado:** en implementación.

**Objetivo:** volver a ejecutar automáticamente la revisión de favoritos cada 30-60
minutos, pero solo para **inspeccionar/listar** notificaciones de artículos añadidos
a favoritos. No se envía ningún mensaje en esta fase.

## Decisiones acordadas

1. `vinted reply` inspecciona notificaciones y no responde. El envío queda para un
   plan posterior.
2. Intervalo aleatorio real: tras cada ejecución se calcula el siguiente disparo con
   `random.randint(30, 60)` minutos. No se usa cron.
3. `REPLY_CRON` se elimina; el intervalo queda documentado como 30-60 min aleatorio.
4. `Data/reply_added_favorites.txt` no es obligatoria en esta fase.
5. Se inspeccionan cuentas desde `Data/<Cuenta>/`, usando el perfil
   `sessions/<Cuenta>/` igual que el resto de comandos.
6. Lock global cross-process para Selenium: ningún job/comando debe pisar sesiones
   activas.
7. Alcance de listado: máximo 40 wrappers
   `data-testid="inbox-notification-intersection-wrapper"` cuyo contenido contenga
   `a sus favoritos`.
8. Flujo por notificación: abrir secuencialmente en pestaña nueva; si la conversación
   ya está respondida (`data-testid="offer-current-price-label"`), detenerse. No
   hacer ninguna acción sobre la notificación.

## No objetivos

- No enviar mensajes ni tocar inputs/botones de conversación.
- No automatizar E2E contra Vinted.
- No modificar `sessions/`.
- No ejecutar `--publish`.

## Cambios previstos

### Fase 1 — Contrato y lock
- Nuevo resultado `FavoriteScanResult`/modelos de notificación en `shared/models.py`.
- Puerto de inspección en `shared/ports.py`; `reply(template)` queda fuera de esta fase.
- `shared/selenium_lock.py`: lock de fichero con `fcntl.flock` en `profiles_dir`.

### Fase 2 — Runtime, handler y adapter
- `run_reply` recorre cuentas de `Data/<Cuenta>`, sin plantilla.
- `reply_favorites` pasa a scan; dry-run simula sin navegador.
- `vinted_replier.py` navega a `/member/notifications`, hace scroll hasta 40
  favoritos, abre pestañas secuencialmente, detecta marcador de respondida y para.
- `runtime.py` y `DriverPort`/helpers mínimos para pestañas/handles, encapsulados.

### Fase 3 — Scheduler y CLI
- `scheduler.py` registra `publicacion_diaria` y `respuesta_favoritos` con
  `max_instances=1`, `coalesce=True` y lock compartido de Selenium.
- `respuesta_favoritos` se reprograma con delay aleatorio real 30-60 min.
- CLI/help actualizados: `reply` inspecciona; `--schedule` arranca ambos jobs.

### Fase 4 — Tests y docs
- Tests unitarios de lock, scheduler, settings, run_reply, handler, CLI.
- Actualizar `CONSTITUTION.md`, `README.md`, `.env.example`, `docs/*`, planes afectados.
- Verificación: `ruff check .`, `ruff format .`, `mypy src tests`, `pytest`.

## Criterios de aceptación

- `vinted reply --dry-run` recorre cuentas sin exigir plantilla ni abrir navegador.
- El modo real navega a `/member/notifications`, recoge máximo 40 favoritos, abre
  pestañas secuencialmente, para al detectar `offer-current-price-label` y no envía
  mensajes.
- El scheduler registra publicación y reply; el próximo reply se programa 30-60 min
  después de cada ejecución.
- Dos comandos/jobs no pisan Selenium gracias al lock global.
- `ruff`, `mypy` y `pytest` en verde.