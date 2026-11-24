# Plan 007 — Respuestas al primer mensaje

**Estado:** estructura implementada; ubicación de la alerta pendiente de confirmar.
El reply automático está retirado temporalmente del barrido y del scheduler
(plan 023); el comando manual `vinted reply` sigue disponible.

**Objetivo:** responder una sola vez a las conversaciones nuevas avisadas por favorito.

**Regla acordada**
- Disparador: alerta que contiene `ha marcado como favorito tu artículo`.
- Solo conversaciones nuevas (sin mensaje saliente previo).
- Plantilla global leída de `Data/reply_added_favorites.txt`.

**Tareas realizadas**
- `config.load_reply_template`.
- `replier.py` con la lógica de detección y envío.
- Logs sin texto de mensajes.

**Pendiente**
- Confirmar si la alerta está en notificaciones, mensajes o ambos.
- Crear `Data/reply_added_favorites.txt` con el texto definitivo.
