# Plan 029 — Franja horaria del reply programado

**Estado:** aprobado.

**Objetivo:** conservar el intervalo aleatorio real de 30-60 minutos entre
ejecuciones del reply programado, pero evitar disparos de madrugada: no se
ejecutará entre las 01:00 y las 08:00 de la zona horaria configurada
(`Europe/Madrid` por defecto).

## Decisiones acordadas

1. La franja bloqueada es `[01:00, 08:00)`: las 08:00 están permitidas y las
   01:00 no.
2. Si el disparo calculado (tras sumar 30-60 min) cae dentro de la franja, se
   difiere a `08:00 + randint(0, 30)` minutos del mismo día local. El resto de
   disparos conserva el intervalo aleatorio de 30-60 min.
3. La franja y el jitter son constantes en `scheduler.py`, igual que el intervalo
   actual; no se añaden variables de entorno. `TIMEZONE` sigue configurándose
   por entorno.
4. La restricción afecta solo al job `respuesta_favoritos` del scheduler. El
   comando manual `vinted reply` sigue funcionando a cualquier hora; la
   publicación diaria no cambia.

## No objetivos

- No cambiar el intervalo aleatorio de 30-60 min ni el trigger de publicación.
- No restringir el comando manual `vinted reply`.
- No automatizar pruebas E2E contra Vinted ni ejecutar `--publish`.
- No modificar `sessions/`.

## Cambios previstos

### Fase 1 — Scheduler

- `scheduler.py`: constantes para el inicio/fin de la franja y el jitter
  matutino; `_next_reply_run()` detecta si el candidato cae en la franja y
  devuelve el disparo diferido. Se reutiliza el `randint` inyectado para mantener
  los tests deterministas. El ajuste se aplica al disparo inicial y a cada
  reprogramación posterior a `run_reply`.

### Fase 2 — Tests

- `tests/unit/test_scheduler.py`: límites exactos (01:00 bloqueado, 08:00
  permitido), disparo de madrugada, franja tardía, paso de medianoche y arranque
  del scheduler dentro de la franja, con una zona horaria distinta de la del
  sistema.

### Fase 3 — Documentación y verificación

- Actualizar `CONSTITUTION.md`, `README.md`, `.env.example`,
  `docs/architecture.md` y `docs/checklist.md`.
- Verificar con `ruff check .`, `ruff format .`, `mypy src tests` y `pytest`.

## Criterios de aceptación

- Ningún disparo del job `respuesta_favoritos` cae en `[01:00, 08:00)` de la
  zona configurada; si el cálculo aleatorio cae ahí, el primer disparo del día
  queda entre 08:00 y 08:30.
- Los disparos fuera de la franja siguen separados por un aleatorio real de
  30-60 min.
- El comando manual y el job de publicación conservan su comportamiento.
- `ruff`, `mypy` y `pytest` en verde.

## Resultado

- `scheduler.py` difiere a las 08:00 + 0-30 min los disparos calculados dentro
  de la franja, tanto al arrancar como al reprogramar tras cada ejecución.
- `ruff check .`, `ruff format .`, `mypy src tests` y `pytest` en verde: 189
  tests. Los tests del reply se adaptaron además a la decisión vigente de
  considerar respondida una conversación con mensajes (commits posteriores al
  plan 028), que había dejado 5 tests fallidos preexistentes.
- Sin `--publish`, sin E2E contra Vinted y sin cambios en `sessions/`.
