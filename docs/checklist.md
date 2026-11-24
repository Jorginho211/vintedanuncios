# Checklist manual de verificación

Antes de dar por bueno un cambio:

1. `poetry run ruff check .`
2. `poetry run mypy src tests`
3. `poetry run pytest`
   - No se commitea si falla alguno de los tres: primero se corrige el código o
     se adaptan el test y la documentación a la decisión vigente. La suite queda
     siempre en verde.
4. Comprobar que los tres archivos reales existen en `Data/` (copiados de los
   `*.example`). Renombrar uno temporalmente y verificar que `vinted --dry-run`
   termina con código 1 y un error que indica qué copiar.
5. `docker compose up -d` y comprobar que Selenium responde en `http://127.0.0.1:4444`.
6. `poetry run vinted --dry-run`
   - Revisar que se listan las cuentas y categorías esperadas.
   - Revisar que los títulos salen de la categoría correcta (incluida la variante `levis`).
   - Revisar que la descripción contiene el texto de `description.txt`, con
     `{{TALLA}}` sustituido por la talla calculada (`W32 | ES 42` o, por
     ejemplo, `M`), y que una medida fuera de tabla aparece en `errors`.
   - Confirmar que no se ha borrado ninguna carpeta ni publicado nada.
7. Si el cambio afecta a Selenium o a los perfiles:
   - `poetry run vinted check-session CuentaA` con `docker compose up -d`.
   - Ver en `http://127.0.0.1:7900` que cargue `https://www.vinted.es` y que
     la sesión sigue iniciada; pulsar Enter y confirmar que el driver se cierra.
   - Repetir `check-session` con la misma cuenta y confirmar que sigue iniciada:
     el perfil se usa in situ, no se copia a `/tmp/rust_mozprofile...`.
   - Si se hizo login en VNC, comprobar que `cookies.sqlite` de `sessions/<Cuenta>/`
     cambia de fecha tras pulsar Enter.
   - Comprobar que un nombre de sesión inexistente termina con código 1.
8. Si el cambio afecta a publicación:
   - Probar con **una** cuenta y **un** anuncio cuyas fotos sean JPEG/PNG/GIF.
     Con `.HEIC`, Vinted muestra un error crítico y el anuncio no se publica.
   - Hacer una copia de `Data/` antes de `--simulate-send`: borra las carpetas de
     los anuncios, pero conserva las de cuenta y categoría.
   - `poetry run vinted --simulate-send`: ver en `http://127.0.0.1:7900` que se
     rellenan todas las secciones, incluido el campo «Talla» con la primera
     opción de Vinted que contenga la talla calculada; confirmar en los logs que **no** se pulsó
     «Subir», que se volvió atrás descartando cambios y que solo desaparecieron
     las carpetas hojas de los anuncios.
   - Con un anuncio sin marca, ver que el desplegable «Marca» se desplaza por la
     lista completa y termina con `Vintage Dressing` en el campo, sin usar el
     buscador; si Vinted no ofrece esa opción, la simulación falla en el paso
     «marca» sin publicar.
   - Comprobar que `--dry-run`, `--simulate-send` y `--publish` son exclusivos:
     combinar dos de ellos termina con código 1.
   - Usar `--publish` solo después de revisar los pasos 6 y 8.
   - Confirmar que la carpeta se borra solo tras el mensaje de éxito de Vinted;
     si el resultado es ambiguo, no se borra y no hay reintentos.
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
13. Revisar que `vinted --help` muestra `publish`, `reply`, `sweep` y
    `--simulate-send`, y que `REPLY_CRON` y `SELENIUM_DATA_DIR` aparecen
    documentadas en `.env.example`.
14. `pip-audit` antes de actualizar dependencias.
