# Plan 002 — Spike de persistencia del perfil Firefox

**Estado:** diagnosticado y corregido en el plan 020; verificación manual pendiente.

**Objetivo:** verificar que el perfil guardado en `sessions/<Cuenta>/` mantiene la sesión iniciada entre dos ejecuciones del contenedor.

**Tareas**
1. Levantar `docker compose up -d`.
2. Iniciar sesión con una cuenta de prueba y cerrar el driver.
3. Volver a crear el driver con el mismo perfil y comprobar que sigue dentro de la cuenta.

**Criterios de aceptación**
- La sesión sobrevive a dos ejecuciones.
- Si no, ajustar `docker-compose.yaml` o el mecanismo de perfil en `browser.py` y documentar el cambio.

## Resultado

El spike detectó el fallo: `options.profile` enviaba el perfil como ZIP a
`/tmp/rust_mozprofile...`, que se borra al cerrar la sesión. Se corrigió usando
el perfil in situ del volumen montado en el plan 020. La comprobación manual con
dos sesiones consecutivas queda recogida en `docs/checklist.md`.
