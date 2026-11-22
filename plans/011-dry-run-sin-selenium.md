# Plan 011 — `--dry-run` sin Selenium

**Estado:** completado (corrección de un fallo detectado al probar con un árbol real).

**Problema:** `runner.run_once` creaba un driver por cuenta incluso en simulación.
Si Docker no estaba levantado, `--dry-run` terminaba con `MaxRetryError` antes de
mostrar los anuncios, contradiciendo el principio de "simulación por defecto"
de `CONSTITUTION.md`.

**Solución aplicada**
- Los drivers se crean solo cuando `publish=True`.
- `publisher.publish_listing` y `replier.reply_to_favorites` aceptan
  `driver: WebDriver | None`; en simulación devuelven antes de usarlo.
- El bucle itera las cuentas detectadas y pasa `drivers.get(cuenta)`.
- Test de regresión en `tests/unit/test_runner.py`: en `--dry-run` no se llama a
  `create_driver` y no se borra la carpeta; con `--publish` se crea un driver y la
  carpeta se borra tras la confirmación simulada.

**Criterio de aceptación:** `poetry run vinted --dry-run` funciona sin contenedor
de Selenium y muestra los anuncios resueltos desde el nombre de archivo.
