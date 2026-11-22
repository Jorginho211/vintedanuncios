# Estándares de desarrollo

- Python 3.12. Código en inglés (`snake_case`, `PascalCase`, `MAYUSCULAS`).
- Comentarios y documentación en español cuando aporten contexto de negocio.
- Ruff para formato y lint; línea máxima de 100 caracteres.
- mypy en modo estricto sobre `src` y `tests`.
- Anotaciones de tipo obligatorias en todas las funciones públicas.
- Los campos ausentes se modelan como `str | None`, nunca como cadenas vacías.
- Capas: `config`, `metadata`, `models`, `scanner` y `selectors` no importan Selenium.
- Manejo de errores: excepciones propias (`CaptionError`, `ConfigError`,
  `MetadataError`, `ScanError`); se capturan en el bucle y se registran con
  identificar de carpeta, sin abortar el resto.
- Logs: identificadores y fechas; **nunca** texto de mensajes de compradores.
- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`).
- Ramas: `main` + ramas cortas para cambios grandes.
- Toda funcionalidad nueva añade un archivo en `plans/` antes de implementarse.
