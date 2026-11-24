# Constitución del proyecto — VintedAnuncios

## 1. Propósito

Herramienta **local** y de uso personal que, desde un árbol de carpetas, publica anuncios en Vinted y responde una sola vez al primer mensaje del comprador cuando recibe una alerta de favorito.

No es un servicio multiusuario, no expone API y no se ejecuta en la nube.

## 2. Principios rectores

1. **Simulación por defecto.** Ninguna acción escribe en Vinted salvo que se pase explícitamente `--publish`. Los modos `--dry-run`, `--simulate-send` y `--publish` son mutuamente exclusivos; `--simulate-send` recorre el formulario real sin pulsar «Subir» y simula las respuestas a favoritos.
2. **El sistema de archivos es la fuente de verdad.** Una carpeta de anuncio existe = anuncio pendiente. Se borra tras la publicación confirmada o al terminar `--simulate-send`, siempre con guarda de ruta: solo `Data/<Cuenta>/<Categoría>/<Anuncio>/`.
3. **Separación de capas.** `shared/` contiene datos y contratos; los handlers de
   `features/` contienen los casos de uso; Selenium y el filesystem viven aislados
   en `adapters/`. Los puertos de `shared/ports.py` definen la frontera.
4. **Sin estado local para las respuestas.** Vinted determina qué conversación fue respondida; solo se escriben logs de auditoría (sin datos personales).
5. **Seguridad por defecto.** Perfiles de navegador fuera de Git, Selenium escuchando solo en `127.0.0.1`, escaneo de secretos, logs sin mensajes de compradores.
6. **Sin evasión de controles de la plataforma.** El riesgo de las condiciones de servicio de Vinted fue revisado y aceptado por el propietario. No se implementan mecanismos anti-CAPTCHA ni de ocultación de automatización. Las pausas configurables de `ActionPacer` existen solo para dar tiempo al DOM y evitar carreras, no para simular comportamiento humano.
7. **Toda decisión importante se consulta.** Cada funcionalidad nueva se registra en `plans/` antes de implementarse.

## 3. Stack tecnológico

| Capa | Elección |
|---|---|
| Lenguaje | Python 3.12 |
| Entorno y dependencias | Poetry (`pyproject.toml`, `poetry.lock`) |
| Automatización | Selenium + Firefox (Docker, `docker-compose.yaml`) |
| Caption | Nombre del archivo de foto; solo `pathlib`, sin librerías de metadatos |
| Scheduler | APScheduler: publicación `0 16 * * *` y favoritos `REPLY_CRON` (`*/15 * * * *`), `Europe/Madrid` configurable por `TIMEZONE` |
| CLI | Typer |
| Calidad | Ruff, mypy estricto, pytest, pre-commit (Ruff + mypy + detect-secrets), pip-audit manual |

## 4. Contrato de datos

### Caption (nombre del archivo de una de las fotos)

```
precio;medidas(ancho x largo);marca(opcional);modelo(opcional)
```

- `;` es siempre separador; no se escapa dentro de los valores.
- Se permite un `;` final y se interpreta como "sin modelo".
- `medidas` en centímetros con formato `50x60`.
- El nombre del archivo es la caption sin la extensión: `24.95;50x60;Nike;35A.JPG`.
- Ejemplos: `25;40x30.JPG`, `25;40x30;Levis.JPG`, `25;40x30;Levis;Air Max 90.JPG`.
- Las fotos se adjuntan ordenadas por nombre, con la foto que lleva la caption
  siempre en primera posición; el resto conserva su orden alfabético.
- Vinted solo acepta JPEG/PNG/GIF: las fotos `.HEIC`/`.HEIF` se rechazan con un
  diálogo de error crítico y no se convierten automáticamente.
- No se contempla el caso "modelo sin marca".

### Configuración

- Los tres archivos reales de `Data/` son obligatorios para publicar o para el
  barrido completo. Se crean copiando `config.json.example`,
  `description.txt.example` y `reply_added_favorites.txt.example`. Si falta alguno (o la plantilla de respuesta
  está vacía), la ejecución se detiene con un error y código de salida 1; no se
  escanea ni se publica. El comando `reply` solo exige el árbol de carpetas de
  cuenta y la plantilla: no lee `config.json` ni `description.txt`; sin cuentas
  avisa y termina con código 0.
- `Data/config.json`: una clave por categoría, con `default`, variantes opcionales por marca (`levis`) y la clave reservada `size` (`pants` o `top`) que elige la tabla de tallas. Falta o valor inválido detiene la ejecución.
- Selección del título: `config.json` usa el nombre de carpeta de categoría completo (puntos literales) + `marca.lower()`; si no hay variante, `default`. El título enviado es `<Marca> <Modelo> <Titulo>`. La marca también se elige en el campo «Marca»; el modelo no existe como campo en Vinted y solo va en el título. Las medidas no se envían.
- Si la caption no tiene marca, el campo «Marca» del formulario se rellena con
  `Vintage Dressing` (constante en el publicador). Ese valor no forma parte de
  la caption ni del título: sin marca, el título es `<Modelo> <Titulo>` con la
  variante `default`. La sugerencia de marca de Vinted se sobrescribe en ese caso.
- El formulario usa la categoría antes del primer punto (`Cortavientos.General` → `Cortavientos`).
- Talla: `width_cm` es el ancho plano de la prenda (media vuelta). La tabla `pants` produce `WXX | ES XX` con `ES = W + 10`; la tabla `top` produce de `XXXS` a `8XL`. Solo `Pantalones Anchos` usa `pants`. Medidas fuera de tabla son error de escaneo. La misma talla se sustituye en `{{TALLA}}` y se busca en el campo «Talla» de Vinted: se elige la primera opción del DOM que contenga `WXX` o `ES XX`; si no existe, no se publica.
- `Data/description.txt`: descripción común a todas las categorías. Si aparece `{{TALLA}}`, se sustituye por la talla calculada.
- `Data/reply_added_favorites.txt`: plantilla global de respuesta. Si falta o está
  vacía, la ejecución termina con error y código 1, también en el comando `reply`.
- Las variables de entorno se leen y validan una sola vez en `shared/settings.py`;
  `config.py` queda reservado a la configuración de dominio de `Data/`. Los nombres
  de entorno van en inglés, igual que los identificadores de código.

### Árbol

```
Data/<Cuenta>/<Categoría>/<Anuncio>/  (solo fotos JPEG/PNG/GIF)
sessions/<Cuenta>/                    (perfil Firefox in situ; ignorado por Git)
```

## 5. Estándares

- Código y variables de entorno en inglés; documentación y logs en español.
- Ruff para formato y lint; mypy en modo estricto.
- Conventional Commits.
- `main` + ramas cortas para cambios grandes.
- Tests unitarios e integración; sin E2E automático contra Vinted.
- No se commitea con `ruff`, `mypy` o `pytest` fallidos: si un test falla, se
  corrige el código o se adaptan el test y la documentación a la decisión
  vigente antes de commitear. La suite queda siempre en verde.
- Cobertura objetivo: 80 % sobre la lógica pura (`config`, `metadata`, `models`, `scanner`).

## 6. Seguridad

- Selenium/VNC publicados solo en `127.0.0.1`.
- Los perfiles de `sessions/` se usan in situ con `-profile` sobre el volumen
  montado: nunca se envían como ZIP a un perfil temporal que se pierde al cerrar.
- `Data/` excluido de Git; solo `Data/.gitkeep` y los tres `*.example` versionados.
- `sessions/` excluido de Git; solo `sessions/.gitkeep` versionado.
- Escaneo de secretos en pre-commit.
- Logs con identificadores y fechas, nunca texto de mensajes de compradores.
- Pausas configurables entre anuncios y entre cuentas por estabilidad.
- Revisión manual de dependencias con `pip-audit`.

## 7. Pendientes documentados

- Confirmar la ubicación exacta de la alerta *"ha marcado como favorito tu artículo"*.
- Verificar manualmente que el perfil conserva el login entre dos sesiones (plan 020).

## 8. Proceso de cambio

Las decisiones estructurales (stack, contrato de datos, capas, seguridad) se consultan al propietario antes de aplicarse. Los cambios funcionales se registran como un plan en `plans/` y se marcan como completados al finalizar.
