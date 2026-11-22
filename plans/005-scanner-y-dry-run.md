# Plan 005 — Scanner y modo simulación

**Estado:** completado.

**Objetivo:** recorrer `Data` y producir anuncios sin tocar Selenium, con la CLI segura por defecto.

**Tareas realizadas**
- `config.py`: carga de `config.json` y `description.txt`; título por categoría y marca (`str.lower()`), con fallback a `default`.
- `scanner.py`: recorrido `Cuenta/Categoría/Anuncio`, ignorando archivos y carpetas ocultas.
- `cli.py`: `--publish`, `--dry-run`, `--schedule`; sin `--publish` no se escribe en Vinted.
- `runner.py`: orquestación y borrado solo tras confirmación.
- `docs/checklist.md`.

**Criterios de aceptación**
- `vinted --dry-run` lista los anuncios y no modifica nada.
- Los archivos `config.json` y `description.txt` no se confunden con anuncios.
