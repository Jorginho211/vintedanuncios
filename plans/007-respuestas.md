# Plan 007 — Respuestas al primer mensaje

**Estado:** completado. La ubicación de la alerta se confirmó en notificaciones
(plan 027) y el envío de la oferta y del mensaje se implementó en el plan 028.
El comando manual `vinted reply` sigue disponible; el scheduler lo programa
según el plan 027.

**Objetivo:** responder una sola vez a las conversaciones nuevas avisadas por favorito.

**Regla acordada**
- Disparador: alerta que contiene `ha marcado como favorito tu artículo`.
- Solo conversaciones nuevas (sin mensaje saliente previo).
- Plantilla global leída de `Data/reply_added_favorites.txt`.

**Tareas realizadas**
- `config.load_reply_template`.
- Detección en `/member/notifications` (plan 027).
- Oferta de 2 € menos y envío de la plantilla con Enter (plan 028).
- Logs sin texto de mensajes.

**Pendiente**
- Verificar manualmente la modal y los selectores del reply con
  `docs/checklist.md` antes de usar `vinted reply --publish`.
- Mantener `Data/reply_added_favorites.txt` con el texto definitivo.
