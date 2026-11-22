# VintedAnuncios

Herramienta local que recorre `Data/<Cuenta>/<Categoría>/<Anuncio>/`, lee la
caption del nombre de cada archivo de foto y publica los anuncios en Vinted. Después responde
una vez al primer mensaje del comprador cuando recibe una alerta de favorito.

**Predeterminado seguro:** sin `--publish` el programa solo valida y muestra lo
que haría. Los archivos de diseño están en `CONSTITUTION.md` y `docs/`.

## Puesta en marcha

`Data/` está ignorado por Git: solo se versionan `Data/.gitkeep` y los archivos
`*.example`. Antes de ejecutar, copia las plantillas a sus nombres reales:

```bash
poetry install
cp Data/config.json.example Data/config.json
cp Data/description.example Data/description.txt
cp Data/reply_added_favorites.example Data/reply_added_favorites.txt
```

| Archivo real | Plantilla versionada | Contenido |
|---|---|---|
| `Data/config.json` | `Data/config.json.example` | Títulos por categoría y variante de marca |
| `Data/description.txt` | `Data/description.example` | Descripción común (se usa tal cual) |
| `Data/reply_added_favorites.txt` | `Data/reply_added_favorites.example` | Plantilla de respuesta a favoritos |

**Los tres archivos son obligatorios.** Si falta alguno, el programa se detiene
con un error que indica qué plantilla copiar y termina con código 1: no escanea,
no publica y no responde. Tampoco funciona si la plantilla de respuesta está vacía.

La simulación no necesita Docker:

```bash
poetry run vinted --dry-run
```

Para publicar de verdad (solo cuando tú lo decidas), levanta Selenium y ejecuta:

```bash
docker compose up -d
poetry run vinted --publish
```

Para dejar el job programado a las 16:00 de `Europe/Madrid`:

```bash
poetry run vinted --publish --schedule
```

## Estado

Proyecto en fase inicial. Los pendientes están listados en la constitución y en
`plans/`.
