# VintedAnuncios

Herramienta local que recorre `Data/<Cuenta>/<Categoría>/<Anuncio>/`, lee la
caption del nombre de cada archivo de foto y publica los anuncios en Vinted.
Además ejecuta `vinted reply` para responder a los favoritos pendientes: ofrece
2 € menos que el precio anterior y envía una plantilla. El scheduler puede
programar ese barrido cada 30-60 minutos de forma aleatoria (planes 027 y 028).

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
| `Data/reply_added_favorites.txt` | `Data/reply_added_favorites.txt.example` | Mensaje enviado a cada favorito pendiente |

**`config.json` y `description.txt` son obligatorios para publicar** (`vinted
publish` y `vinted sweep`). Si falta alguno, el programa se detiene con un error
que indica qué plantilla copiar y termina con código 1: no escanea ni publica.

`vinted reply` responde notificaciones de favoritos por cuenta: solo necesita
el árbol `Data/<Cuenta>/` y, salvo en `--dry-run`, la plantilla
`reply_added_favorites.txt`. No lee `config.json` ni `description.txt`. Si no hay
carpetas de cuenta, avisa y termina con código 0.

## Uso con Docker

En la máquina de instalación solo hace falta Docker con el plugin Compose. Antes
de arrancar, crea los directorios compartidos y copia las plantillas de `Data/`:

```bash
mkdir -p Data sessions logs
cp Data/config.json.example Data/config.json
cp Data/description.txt.example Data/description.txt
cp Data/reply_added_favorites.txt.example Data/reply_added_favorites.txt
cp .env.example .env   # opcional: TIMEZONE, pausas, esperas...
```

`logs/` debe existir en el host: si lo crea Compose automáticamente queda de
`root` y el usuario del contenedor no podría escribir `vinted.log`.

El compose define dos servicios:

- `selenium`: Firefox remoto y noVNC, publicados solo en `127.0.0.1:4444` y
  `127.0.0.1:7900`. Tiene un healthcheck sobre `/status`.
- `vinted`: el scheduler, arranca como `vinted --publish --schedule` (decisión
  explícita del propietario, plan 024). Se levanta con `docker compose up -d`
  y se reinicia automáticamente.

Para ejecutar cualquier comando de la CLI en el mismo entorno:

```bash
docker compose build
docker compose run --rm vinted --dry-run
docker compose run --rm vinted publish --dry-run
docker compose run --rm vinted reply --dry-run
docker compose run --rm -it vinted check-session CuentaA
docker compose logs -f vinted
```

El primer `vinted` es el nombre del servicio; la imagen ya tiene `vinted` como
`ENTRYPOINT`, por eso los argumentos se pasan directamente. `-it` hace falta en
`check-session` porque el comando espera a que pulses Enter. Para abrir una
shell: `docker compose run --rm --entrypoint /bin/bash vinted -c 'bash'`
(si no se pasa `-c`, Compose añade los argumentos del scheduler).

Se comparte el contenido con el host:

| Host | Contenedor | Uso |
|---|---|---|
| `./Data` | `/Data` | lectura/escritura en la app, solo lectura en Selenium |
| `./sessions` | `/sessions` | perfiles de Firefox, lectura/escritura en ambos |
| `./logs` | `/app/logs` | `vinted.log` de la app |

Dentro de Compose se fuerzan `SELENIUM_URL=http://selenium:4444`, `DATA_DIR=/Data`,
`SELENIUM_DATA_DIR=/Data`, `PROFILES_DIR=/sessions` y
`SELENIUM_PROFILES_DIR=/sessions`; el resto de variables se leen de `.env` (si
existe). El usuario de la app es `${UID:-1000}:${GID:-1000}` del host; Selenium
conserva el usuario `1000:1000` de la configuración anterior.

Para arrancar solo el grid y comprobarlo:

```bash
docker compose up -d selenium
curl http://127.0.0.1:4444/status
```

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
--simulate-send` solo inspecciona y registra lo que haría, sin escribir en Vinted.
Haz una copia de `Data/` si quieres repetir la prueba.

Para publicar de verdad (solo cuando tú lo decidas), levanta Selenium y ejecuta:

```bash
docker compose up -d
poetry run vinted --publish
```

Para dejar programada la publicación a las 16:00 de `Europe/Madrid` con
`--publish`:

```bash
poetry run vinted --publish --schedule      # en el host
docker compose up -d vinted                 # en contenedor (arranca con --publish --schedule)
```

Con `--schedule` se registran `publicacion_diaria` (16:00, `TIMEZONE`) y
`respuesta_favoritos`, que se reprograma con un retraso aleatorio real de 30-60
minutos tras cada ejecución. Ambos jobs usan un lock global de Selenium para no
pisar sesiones.

## Publicar y responder por separado

```bash
# Solo publica anuncios pendientes; no inspecciona favoritos
poetry run vinted publish --dry-run

# Solo inspecciona favoritos; no escanea ni publica ni escribe en Vinted
poetry run vinted reply --dry-run

# Barrido de publicación bajo demanda (igual que `vinted --dry-run`)
poetry run vinted sweep --dry-run

# Barrido real sin pulsar Subir (borra las carpetas de anuncio)
poetry run vinted sweep --simulate-send

# Responde favoritos de verdad (único modo que escribe en Vinted)
poetry run vinted reply --publish
```

`vinted`, `publish` y `sweep` publican sin revisar favoritos. `vinted reply`
inspecciona notificaciones en `/member/notifications`, recoge hasta 40 wrappers
con “a sus favoritos” y abre cada una en pestaña secuencialmente. En cada
conversación pendiente lee el precio anterior del placeholder de la modal,
ofrece 2 € menos con coma decimal y envía `reply_added_favorites.txt` pulsando
Enter. Al detectar `offer-current-price-label` no actúa y detiene el barrido de
esa cuenta. Solo `--publish` realiza esas escrituras: los demás modos registran
lo que harían.

## Verificar una sesión

Para comprobar a mano si sigues iniciado en Vinted con un perfil guardado, indica
el nombre de la carpeta dentro de `sessions/` (por ejemplo `sessions/CuentaA`):

```bash
# En el host:
docker compose up -d
poetry run vinted check-session CuentaA

# O íntegramente en Docker:
docker compose run --rm -it vinted check-session CuentaA
```

El comando abre `https://www.vinted.es` en el Firefox del contenedor. Mira la
pantalla en `http://127.0.0.1:7900` y pulsa Enter en la terminal para cerrar el
navegador. Si la carpeta de sesión no existe, termina con un error y código 1.
Este comando solo navega: no publica, no responde y no inicia sesión por ti.

Firefox usa `sessions/<Cuenta>` **in situ** (`-profile` sobre el volumen
`./sessions:/sessions`), no una copia temporal: el login y las cookies que hagas
en VNC se conservan al pulsar Enter y sirven para la siguiente ejecución. La
carpeta debe ser escribible por el usuario del contenedor (uid 1000, según
`docker-compose.yaml`); el factory la crea con permisos `777` si aún no existe, y
avisa si ya existe sin permiso de escritura para otros usuarios. El grid mantiene la sesión viva 2
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

La respuesta de favoritos se programa con intervalo aleatorio real de 30-60
minutos entre ejecuciones. Las pausas `SELENIUM_ACTION_DELAY_*` se aplican a todo
el flujo con navegador (formulario y reply) para dar tiempo al
DOM a actualizarse; `--dry-run` no usa Selenium y por eso no se retrasa. Pon ambos
valores a `0` para desactivarlas.

## Estado

Proyecto en fase inicial. Los pendientes están listados en la constitución y en
`plans/`.
