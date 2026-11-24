# VintedAnuncios

Herramienta local que recorre `Data/<Cuenta>/<Categoría>/<Anuncio>/`, lee la
caption del nombre de cada archivo de foto y publica los anuncios en Vinted.
Además ofrece `vinted reply` para responder favoritos de forma manual; esa parte
está retirada temporalmente de los barridos y del scheduler (plan 023).

**Predeterminado seguro:** sin `--publish` el programa solo valida y muestra lo
que haría. Los tres modos (`--dry-run`, `--simulate-send`, `--publish`) son
mutuamente exclusivos. Los archivos de diseño están en `CONSTITUTION.md` y `docs/`.

## Puesta en marcha

`Data/` está ignorado por Git: solo se versionan `Data/.gitkeep` y los archivos
`*.example`. Antes de ejecutar, copia las plantillas a sus nombres reales:

```bash
poetry install
cp Data/config.json.example Data/config.json
cp Data/description.txt.example Data/description.txt
cp Data/reply_added_favorites.txt.example Data/reply_added_favorites.txt
```

| Archivo real | Plantilla versionada | Contenido |
|---|---|---|
| `Data/config.json` | `Data/config.json.example` | Títulos por categoría y variante de marca |
| `Data/description.txt` | `Data/description.txt.example` | Descripción común (se usa tal cual) |
| `Data/reply_added_favorites.txt` | `Data/reply_added_favorites.txt.example` | Plantilla de respuesta a favoritos |

**`config.json` y `description.txt` son obligatorios para publicar** (`vinted
publish` y `vinted sweep`). Si falta alguno, el programa se detiene con un error
que indica qué plantilla copiar y termina con código 1: no escanea ni publica.
Esos barridos ya no leen la plantilla de respuesta.

`vinted reply` solo necesita las carpetas de cuenta en `Data/` y la plantilla de
respuesta: no lee `config.json` ni `description.txt`. Si no hay carpetas de cuenta,
avisa y termina con código 0. Si la plantilla falta o está vacía, termina con
código 1.

Las fotos deben estar en **JPEG, PNG o GIF**. Vinted rechaza `.HEIC`/`.HEIF`
con un diálogo de error crítico; convierte las fotos antes de ponerlas en la
carpeta del anuncio. El título se construye como `<Marca> <Modelo> <Titulo>`,
donde `Titulo` sale de `config.json` (categoría completa y variante de marca).
Si la caption no lleva marca, el formulario usa `Vintage Dressing` en el campo
«Marca»; esa marca no se añade al título.

La simulación sin navegador no necesita Docker:

```bash
poetry run vinted --dry-run
```

Para recorrer el formulario real **sin pulsar «Subir»**, levanta Selenium y usa:

```bash
docker compose up -d
poetry run vinted --simulate-send
```

Este modo rellena fotos, título, descripción, precio, categoría, marca, color,
estado y envío; vuelve atrás descartando los cambios y borra únicamente las
carpetas `Data/<Cuenta>/<Categoría>/<Anuncio>/`. Conserva las carpetas de cuenta
y de categoría. Los barridos ya no revisan favoritos; `vinted reply
--simulate-send` simula las respuestas sin escribir en Vinted.
Haz una copia de `Data/` si quieres repetir la prueba.

Para publicar de verdad (solo cuando tú lo decidas), levanta Selenium y ejecuta:

```bash
docker compose up -d
poetry run vinted --publish
```

Para dejar programada la publicación a las 16:00 de `Europe/Madrid` con
`--publish`:

```bash
poetry run vinted --publish --schedule
```

El job de favoritos está retirado temporalmente (plan 023): `--schedule` registra
sólo `publicacion_diaria`.

## Publicar y responder por separado

```bash
# Solo publica anuncios pendientes; no revisa favoritos
poetry run vinted publish --dry-run

# Revisa favoritos en cada cuenta; no escanea ni publica (bajo demanda)
poetry run vinted reply --dry-run

# Barrido de publicación bajo demanda (igual que `vinted --dry-run`)
poetry run vinted sweep --dry-run

# Barrido real sin pulsar Subir (borra las carpetas de anuncio)
poetry run vinted sweep --simulate-send
```

`vinted`, `publish` y `sweep` publican sin responder favoritos. El reply queda
como acción manual con `vinted reply` y no acepta `--schedule`. `REPLY_CRON` se
conserva en la configuración (`*/15 * * * *` por defecto) pero está reservada e
inactiva: el job de favoritos y su bloqueo compartido están retirados (plan 023).

## Verificar una sesión

Para comprobar a mano si sigues iniciado en Vinted con un perfil guardado, indica
el nombre de la carpeta dentro de `sessions/` (por ejemplo `sessions/CuentaA`):

```bash
docker compose up -d
poetry run vinted check-session CuentaA
```

El comando abre `https://www.vinted.es` en el Firefox del contenedor. Mira la
pantalla en `http://127.0.0.1:7900` y pulsa Enter en la terminal para cerrar el
navegador. Si la carpeta de sesión no existe, termina con un error y código 1.
Este comando solo navega: no publica, no responde y no inicia sesión por ti.

Firefox usa `sessions/<Cuenta>` **in situ** (`-profile` sobre el volumen
`./sessions:/sessions`), no una copia temporal: el login y las cookies que hagas
en VNC se conservan al pulsar Enter y sirven para la siguiente ejecución. La
carpeta debe ser escribible por el usuario `seluser` del contenedor (uid 1200);
el factory la crea con permisos `777` si aún no existe, y avisa si ya existe sin
permiso de escritura para otros usuarios. El grid mantiene la sesión viva 2
horas (`SE_NODE_SESSION_TIMEOUT=7200`) para dar tiempo a iniciar sesión. Tras
cambiar `docker-compose.yaml`, ejecuta `docker compose up -d` para recrear el
contenedor.

## Variables de entorno

Todas se leen una sola vez al arrancar y se validan en `shared/settings.py`.
Los nombres siguen el mismo patrón en inglés que el código; `.env.example` los
documenta con sus valores por defecto:

| Variable | Default | Uso |
|---|---|---|
| `DATA_DIR` | `Data` | Árbol de anuncios en el host |
| `SELENIUM_DATA_DIR` | `/Data` | Ruta de `Data/` dentro del contenedor |
| `PROFILES_DIR` | `sessions` | Perfiles de Firefox por cuenta en el host |
| `SELENIUM_PROFILES_DIR` | `/sessions` | Misma carpeta dentro del contenedor |
| `SELENIUM_URL` | `http://127.0.0.1:4444` | Grid de Selenium |
| `SELENIUM_WAIT_SECONDS` | `15` | Espera máxima del navegador |
| `SELENIUM_ACTION_DELAY_MIN` | `1.0` | Pausa mínima entre acciones de Selenium |
| `SELENIUM_ACTION_DELAY_MAX` | `2.0` | Pausa máxima entre acciones de Selenium |
| `PAUSE_BETWEEN_LISTINGS` | `0` | Pausa entre anuncios |
| `PAUSE_BETWEEN_ACCOUNTS` | `0` | Pausa entre cuentas |
| `TIMEZONE` | `Europe/Madrid` | Zona horaria de los jobs (`TZ` es ignorada) |
| `REPLY_CRON` | `*/15 * * * *` | Reservada: el job de favoritos está retirado |

Las pausas `SELENIUM_ACTION_DELAY_*` se aplican a todo el flujo con navegador
(formulario y, en `vinted reply`, favoritos) para dar tiempo al DOM a actualizarse;
`--dry-run` no usa Selenium y por eso no se retrasa. Pon ambos valores a `0` para
desactivarlas.

## Estado

Proyecto en fase inicial. Los pendientes están listados en la constitución y en
`plans/`.
