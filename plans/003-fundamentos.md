# Plan 003 — Fundamentos del proyecto

**Estado:** completado.

**Objetivo:** dejar la base instalable, con calidad y configuración inicial.

**Tareas realizadas**
- `pyproject.toml` con Poetry, Ruff, mypy estricto, pytest y pre-commit.
- Estructura `src/`, `tests/`, `docs/`, `plans/`, `Data/` y `sessions/`.
- `.gitignore`, `.env.example`, `sessions/.gitkeep`.
- `CONSTITUTION.md`, `AGENTS.md` y documentación inicial.
- `docker-compose.yaml` restringido a `127.0.0.1`.

**Criterios de aceptación**
- `poetry install` funciona.
- Los comandos de `AGENTS.md` están disponibles.
