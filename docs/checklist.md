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
7. Si el cambio afecta a Selenium o a los perfiles:
   - `poetry run vinted check-session CuentaA` con `docker compose up -d`.
   - Ver en `http://127.0.0.1:7900` que cargue `https://www.vinted.es` y que
     la sesión sigue iniciada; pulsar Enter y confirmar que el driver se cierra.
   - Comprobar que un nombre de sesión inexistente termina con código 1.
8. Si el cambio afecta a publicación:
   - Probar con **una** cuenta y **un** anuncio.
   - Usar `--publish` solo después de revisar el paso 6.
   - Confirmar que la carpeta se borra solo tras el mensaje de éxito de Vinted.
9. Si el cambio afecta a respuestas:
   - Confirmar que la plantilla existe en `Data/reply_added_favorites.txt`.
   - Verificar que solo se responde a conversaciones nuevas con la alerta acordada.
   - Comprobar que los logs no contienen texto de mensajes.
10. Comprobar los comandos separados en simulación:
    - `poetry run vinted publish --dry-run`: publica anuncios, no responde favoritos.
    - `poetry run vinted reply --dry-run`: recorre las carpetas de cuenta, no
      escanea ni publica.
    - `poetry run vinted sweep --dry-run`: hace ambas cosas como `vinted --dry-run`.
11. Renombrar temporalmente `Data/config.json`: `vinted reply --dry-run` debe seguir
    terminando con código 0, mientras `vinted publish --dry-run` termina con código 1.
12. Con `Data/` sin carpetas de cuenta, `vinted reply --dry-run` avisa y termina con
    código 0; sin plantilla de respuesta, termina con código 1.
13. Revisar que `vinted --help` muestra `publish`, `reply` y `sweep`, y que
    `REPLY_CRON` aparece documentada en `.env.example`.
14. `pip-audit` antes de actualizar dependencias.
