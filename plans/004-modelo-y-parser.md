# Plan 004 — Modelo de datos y parser de caption

**Estado:** completado y validado con la foto fixture `24.95;50x60;Nike;35A.HEIC`.

**Contrato implementado**

```
precio;medidas(ancho x largo);marca(opcional);modelo(opcional)
```

- `;` siempre separa; se tolera un `;` final como "sin modelo".
- Medidas en centímetros con formato `50x60`.
- La caption se toma del nombre del archivo (sin extensión); sin metadatos.
- No se valida el caso "modelo sin marca" (acordado que no puede ocurrir).

**Tareas realizadas**
- `models.py` con `Caption`, `Listing`, `ScanResult`, `PublishResult`, `ReplyResult`.
- `metadata.py` con `parse_caption`, `caption_from_filename` y `parse_caption_from_filename`, solo con stdlib.
- Tests unitarios de los cuatro casos de marca/modelo y de formatos inválidos.

**Pendiente**
- Destino del campo `modelo` en el formulario de Vinted.
