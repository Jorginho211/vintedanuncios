# Checklist manual de verificación

Antes de dar por bueno un cambio:

1. `poetry run ruff check .`
2. `poetry run mypy src tests`
3. `poetry run pytest`
4. Comprobar que los tres archivos reales existen en `Data/` (copiados de los
   `*.example`). Renombrar uno temporalmente y verificar que `vinted --dry-run`
   termina con código 1 y un error que indica qué copiar.
5. `docker compose up -d` y comprobar que Selenium responde en `http://127.0.0.1:4444`.
6. `poetry run vinted --dry-run`
   - Revisar que se listan las cuentas y categorías esperadas.
   - Revisar que los títulos salen de la categoría correcta (incluida la variante `levis`).
   - Revisar que la descripción contiene el texto de `description.txt`.
   - Confirmar que no se ha borrado ninguna carpeta ni publicado nada.
7. Si el cambio afecta a Selenium:
   - Probar con **una** cuenta y **un** anuncio.
   - Usar `--publish` solo después de revisar el paso 6.
   - Confirmar que la carpeta se borra solo tras el mensaje de éxito de Vinted.
8. Si el cambio afecta a respuestas:
   - Confirmar que la plantilla existe en `Data/reply_added_favorites.txt`.
   - Verificar que solo se responde a conversaciones nuevas con la alerta acordada.
   - Comprobar que los logs no contienen texto de mensajes.
9. `pip-audit` antes de actualizar dependencias.
