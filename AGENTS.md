# AGENTS.md — VintedAnuncios

Herramienta local para publicar anuncios en Vinted y responder al primer mensaje
del comprador. Python + Poetry + Selenium + APScheduler + Typer, sin librerías de metadatos.

## Comandos

- `poetry install`
- `poetry run ruff check .` y `poetry run ruff format .`
- `poetry run mypy src tests`
- `poetry run pytest`
- `poetry run vinted --dry-run` (valor por defecto, seguro)
- `poetry run vinted --publish` (solo con autorización explícita)

## Reglas

- Nunca ejecutar `--publish` salvo petición explícita del usuario.
- No modificar el contenido de `sessions/`; solo `sessions/.gitkeep` está versionado.
- No automatizar pruebas E2E contra Vinted; usar `docs/checklist.md`.
- Código en inglés; documentación y logs en español.
- `scanner`, `metadata`, `config` y `models` NO importan Selenium.
- Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`...).
- Toda funcionalidad nueva: crear un plan en `plans/` antes de implementar.
- Decisiones estructurales: preguntar al usuario, no decidir en solitario.
- No escribir secretos en el repositorio.
- Al cambiar una decisión, actualizar `CONSTITUTION.md` y `docs/`.
