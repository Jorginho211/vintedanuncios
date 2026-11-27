# Constitución del proyecto — VintedAnuncios

## 1. Propósito

Herramienta **local** y de uso personal que, desde un árbol de carpetas, publica anuncios en Vinted. También revisa notificaciones de favoritos por cuenta (`vinted reply`): abre cada conversación pendiente, ofrece 2 € menos que el precio anterior y envía una plantilla. Esa escritura solo ocurre con `--publish` (planes 027 y 028).

No es un servicio multiusuario, no expone API y no se ejecuta en la nube.

## 2. Principios rectores

1. **Simulación por defecto.** Ninguna acción escribe en Vinted salvo que se pase explícitamente `--publish`. Los modos `--dry-run`, `--simulate-send`, `--check-submit` y `--publish` son mutuamente exclusivos; `--simulate-send` recorre el formulario real sin pulsar «Subir» y `--check-submit` solo diagnostica el estado del formulario antes de pulsarlo. En `reply`, solo `--publish` pulsa la oferta y envía el mensaje: los demás modos solo inspeccionan y registran lo que harían. El diagnóstico no borra carpetas; `--simulate-send` sí las borra al terminar un barrido de publicación.
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
| Scheduler | APScheduler: publicación `0 16 * * *` y respuesta de favoritos con intervalo aleatorio real de 30-60 min, `Europe/Madrid` configurable por `TIMEZONE` (planes 027 y 028) |
| CLI | Typer |
| Calidad | Ruff, mypy estricto, pytest, pre-commit (Ruff + mypy + detect-secrets), pip-audit manual |
| Contenedores | `Dockerfile` (solo dependencias de producción) + `docker-compose.yaml` con `selenium` y `vinted` (plan 024) |

El servicio `vinted` del compose arranca con `--publish --schedule` por decisión
explícita del propietario. No cambia el principio de simulación por defecto: el
que invoca la CLI en el host o con `docker compose run` sigue necesitando pasar
`--publish` para escribir en Vinted.

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

- `config.json` y `description.txt` son obligatorios para publicar con `vinted`
  o `vinted sweep`; se crean copiando sus respectivos `*.example`. Si falta
  alguno, la ejecución se detiene con error y código de salida 1; no se escanea
  ni se publica. `reply_added_favorites.txt` no se lee en esos barridos.
- El comando manual `reply` solo exige el árbol de carpetas de cuenta; en modos
  reales también exige la plantilla: no lee `config.json` ni `description.txt`;
  sin cuentas avisa y termina con código 0.
- `Data/config.json`: una clave por categoría, con `default`, variantes opcionales por marca (`levis`) y la clave reservada `size` (`pants` o `top`) que elige la tabla de tallas. Falta o valor inválido detiene la ejecución.
- Selección del título: `config.json` usa el nombre de carpeta de categoría completo (puntos literales) + `marca.lower()`; si no hay variante, `default`. El título enviado es `<Marca> <Modelo> <Titulo>`. La marca también se elige en el campo «Marca»; el modelo no existe como campo en Vinted y solo va en el título. Las medidas no se envían.
- Si la caption no tiene marca, el campo «Marca» del formulario se rellena con
  `Vintage Dressing` (constante en el publicador). Ese valor no forma parte de
  la caption ni del título: sin marca, el título es `<Modelo> <Titulo>` con la
  variante `default`. La sugerencia de marca de Vinted se sobrescribe en ese caso.
  El buscador de Vinted no ofrece esa marca: se abre el desplegable y se recorre
  el listado con scroll hasta encontrar una opción cuyo texto, normalizado en
  minúsculas, coincida; si no aparece, se informa del error sin publicar.
- El formulario usa la categoría antes del primer punto (`Cortavientos.General` → `Cortavientos`).
- Talla: `width_cm` es el ancho plano de la prenda (media vuelta) y `length_cm` el largo. La tabla `pants` va de W23 a W38 (28,58–48,90 cm de ancho plano, `W × 1,27`) y produce `WXX | ESXX` con `ES = W + 10`. La tabla `top` es vintage y usa una matriz ancho × largo de `XXXS` a `XXXL`: el ancho manda y un largo tres bandas o más más corto baja una talla; los extremos de `XXXS`/`XXXL` quedan abiertos. Solo `Pantalones Anchos` usa `pants`. Medidas fuera de tabla son error de escaneo. La misma talla se sustituye en `{{TALLA}}` y se busca en el campo «Talla» de Vinted: se elige la primera opción del DOM que contenga `WXX` o `ESXX`; si no existe, no se publica.
- `Data/description.txt`: descripción común a todas las categorías. Si aparece `{{TALLA}}`, se sustituye por la talla calculada.
- `Data/reply_added_favorites.txt`: texto que se envía a cada favorito pendiente.
  `vinted reply --dry-run` no lo exige; los modos reales sí.
- Las variables de entorno se leen y validan una sola vez en `shared/settings.py`;
  `config.py` queda reservado a la configuración de dominio de `Data/`. Los nombres
  de entorno van en inglés, igual que los identificadores de código. La inspección
  de favoritos no usa cron: se programa con intervalo aleatorio real de 30-60 min.

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
- En Docker, `Data/`, `sessions/` y `logs/` se comparten con el host mediante
  volúmenes; `.env`, datos y perfiles quedan fuera del contexto de build.
- Los perfiles de `sessions/` se usan in situ con `-profile` sobre el volumen
  montado: nunca se envían como ZIP a un perfil temporal que se pierde al cerrar.
- `Data/` excluido de Git; solo `Data/.gitkeep` y los tres `*.example` versionados.
- `sessions/` excluido de Git; solo `sessions/.gitkeep` versionado.
- Escaneo de secretos en pre-commit.
- Logs con identificadores y fechas, nunca texto de mensajes de compradores.
- Pausas configurables entre anuncios y, en `vinted reply`, entre cuentas por estabilidad.
- Lock global cross-process de Selenium (`sessions/.selenium.lock`) para evitar solapes entre jobs y comandos manuales.
- Revisión manual de dependencias con `pip-audit`.

## 7. Pendientes documentados

- Confirmar manualmente los selectores de la modal de oferta y del composer con el checklist antes de usar `vinted reply --publish` (plan 028).
- Verificar manualmente que el perfil conserva el login entre dos sesiones (plan 020).

## 8. Proceso de cambio

Las decisiones estructurales (stack, contrato de datos, capas, seguridad) se consultan al propietario antes de aplicarse. Los cambios funcionales se registran como un plan en `plans/` y se marcan como completados al finalizar.
