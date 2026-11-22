# Plan 012 — Archivos de ejemplo y validación obligatoria

**Estado:** completado.

**Objetivo:** que un clon nuevo sepa qué archivos crear y que el programa se
detenga con un error claro si falta alguno, en lugar de publicar con datos
incompletos u omitir el paso de respuestas.

**Tareas realizadas**
1. Añadir `Data/config.json.example`, `Data/description.example` y
   `Data/reply_added_favorites.example` como plantillas independientes: el
   propietario puede editarlas libremente y no deben coincidir con los reales.
2. Eximir los `*.example` de la regla `Data/*` en `.gitignore`.
3. `config.validate_data_dir()`: comprobar los tres archivos obligatorios antes
   de escanear o publicar.
4. `config.load_reply_template()` pasa a exigir la plantilla (ya no devuelve
   `None`) y falla si está vacía.
5. `runner.run_once()` valida al inicio y propaga `ConfigError`.
6. `cli.main()` detecta `ConfigError`, muestra el error por stderr y termina con
   código 1, tanto en ejecución puntual como con `--schedule`.
7. Documentar el procedimiento de copia en `README.md`, `CONSTITUTION.md` y
   `docs/`, con tests de regresión.
