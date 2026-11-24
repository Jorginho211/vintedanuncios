# Plan 023 — Retirada temporal del reply automático

**Estado:** completado.

**Objetivo:** dejar de responder favoritos en los barridos y en el scheduler porque la
funcionalidad no está completa ni probada, sin perder el trabajo ya implementado.

**Decisiones acordadas con el propietario**
1. Se retira sólo la parte automática: el job `respuesta_favoritos` y la fase de
   favoritos de `vinted` / `vinted sweep`.
2. Se conserva el comando bajo demanda `vinted reply` con toda su lógica, sus
   selectores y sus tests. El código se puede recuperar íntegro desde Git si se
   decide reactivar el barrido.
3. `Data/reply_added_favorites.txt` y su plantilla `.example` se conservan: el
   comando manual sigue necesitándolos. El archivo real no se modifica.
4. Se conservan `REPLY_CRON` y `PAUSE_BETWEEN_ACCOUNTS`. `REPLY_CRON` queda
   documentada como reservada e inactiva; `PAUSE_BETWEEN_ACCOUNTS` sigue en uso
   por `vinted reply`.

## Cambios por fase

### Fase 1 — Orquestación y scheduler
- `features/run_sweep/handler.py`: `run_sweep` pasa a ser un alias de
  `run_publish`; no lee la plantilla ni llama a `_reply`. `run_reply` y `_reply`
  permanecen para el comando manual.
- `scheduler.py`: un solo job (`publicacion_diaria`) sin `Lock` ni validación de
  `REPLY_CRON` en el arranque.

### Fase 2 — CLI
- Textos de ayuda actualizados: `vinted`, `publish` y `sweep` publican; `reply`
  sigue siendo una acción manual y no acepta `--schedule`.

### Fase 3 — Pruebas y documentación
- Tests de barrido y scheduler adaptados al job único y a la ausencia de reply.
- Tests de `run_reply`, CLI de `reply`, selectores y plantilla sin cambios.
- Actualizados `CONSTITUTION.md`, `README.md`, `.env.example`,
  `docs/architecture.md`, `docs/testing.md`, `docs/checklist.md` y los planes
  007 y 015.

## Criterios de aceptación
- `ruff check`, `ruff format --check`, `mypy src tests` y `pytest` en verde.
- `vinted --dry-run` y `vinted sweep --dry-run` publican sin responder favoritos
  ni abrir un segundo driver por cuenta.
- `vinted reply --dry-run` sigue recorriendo las cuentas con su plantilla.
- `--schedule` registra únicamente `publicacion_diaria`.
- Sin cambios en `sessions/`, sin `--publish` y sin prueba E2E contra Vinted.

## Resultado

- `ruff check`, `ruff format --check`, `mypy src tests` y `pytest` en verde:
  149 tests, 98 % de cobertura sobre la lógica pura medida.
- Comprobado en `--dry-run`: `vinted`, `vinted sweep` y `vinted reply` terminan
  con código 0; los dos primeros no abren navegador y el tercero simula el reply
  manual.
- Sin cambios en `sessions/`, sin `--publish` y sin prueba E2E contra Vinted.
