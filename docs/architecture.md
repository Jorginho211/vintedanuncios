# Arquitectura

## Visión general

El proceso se lanza una vez al día o bajo demanda. Por defecto trabaja en modo
simulación; solo con `--publish` interactúa con Vinted.

```
scheduler.py (16:00 Europe/Madrid)
        |
        v
   runner.run_once()
        |
        +-- config.load_config(Data/)  -> títulos y descripción
        |
        +-- scanner.scan(Data/)        -> Listing[]  (sin Selenium)
        |
        +-- por cuenta (secuencial):
              browser.create_driver(sessions/<Cuenta>)
              publisher.publish(...)
              si exito y --publish -> borrar carpeta del anuncio
        |
        +-- replier.reply_to_favorites(...)  (plantilla de Data/reply_added_favorites.txt)
```

## Componentes

| Módulo | Responsabilidad | ¿Toca Selenium? |
|---|---|---|
| `models` | Estructuras de datos inmutables | No |
| `metadata` | Parseo de la caption desde el nombre del archivo | No |
| `config` | Carga de `config.json` y `description.txt`; selección de título | No |
| `scanner` | Recorrido del árbol y construcción de `Listing` | No |
| `selectors` | Selectores CSS y textos disparadores centralizados | No |
| `browser` | Creación y cierre del driver por cuenta | Sí |
| `publisher` | Relleno del formulario y publicación | Sí |
| `replier` | Detección de favoritos y envío de la plantilla | Sí |
| `runner` | Orquestación del barrido | Sí (indirecto) |
| `scheduler` | Trigger cron y control de solapamientos | No |
| `cli` | Interfaz Typer | No |
| `logging_conf` | Configuración de logs | No |

## Contrato de datos

Caption: `precio;medidas(ancho x largo);marca(opcional);modelo(opcional)`,
contenida en el **nombre del archivo**: `24.95;50x60;Nike;35A.HEIC`.
Medidas en cm (`50x60`). `;` siempre separa; se tolera un `;` final. No se valida
el caso "modelo sin marca" porque se acordó que no puede ocurrir.

Título: categoría (nombre de carpeta exacto, los puntos son literales) +
`marca.lower()`; si la clave no existe, `default`.

Descripción: contenido literal de `Data/description.txt`. Si el texto incluye
`{{TALLA}}`, se deja tal cual hasta una iteración futura.

Respuesta: contenido literal de `Data/reply_added_favorites.txt`.

Los tres archivos de configuración (`config.json`, `description.txt` y
`reply_added_favorites.txt`) son obligatorios: `validate_data_dir()` se ejecuta
antes de escanear y `cli` termina con código 1 si falta alguno. Las plantillas
versionadas son `*.example` en `Data/`.

## Decisiones

- Procesamiento **secuencial** de cuentas (una sola sesión activa por vez).
- Pausas configurables por estabilidad, no para evadir controles.
- Un error en un anuncio se registra y no aborta el barrido.
- Borrado real de la carpeta **solo** tras confirmación de Vinted y con `--publish`.
- Sin base de datos local: el estado de las conversaciones lo determina Vinted.
- `max_instances=1` y `coalesce=True` en el scheduler.

## Riesgos conocidos / pendientes

- Los selectores de `selectors.py` son provisionales: validar contra la web real.
- La ubicación de la alerta de favorito está pendiente de confirmar.
- La caption se lee del nombre del archivo con `pathlib.stem`; no se usan metadatos ni librerías externas.
- El perfil de Firefox en `sessions/<Cuenta>/` debe verificarse entre ejecuciones.
- Destino del campo `modelo` en el formulario de Vinted: pendiente.
