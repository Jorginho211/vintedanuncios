# Seguridad

- Selenium y VNC publicados **solo en `127.0.0.1`** (sin contraseña en VNC,
  decisión del propietario; el riesgo queda aceptado y documentado).
- En Docker, la app alcanza el grid por la red interna (`http://selenium:4444`);
  no se publican puertos adicionales. `Data/` se monta solo lectura en Selenium
  y lectura/escritura en la app.
- `.dockerignore` evita que `.env`, `Data/`, `sessions/` y `logs/` entren en el
  contexto de build de la imagen.
- El scheduler del contenedor corre con `--publish --schedule` por decisión
  explícita del propietario (plan 024); cualquier otra ejecución sigue en
  simulación salvo que se pase `--publish`.
- `Data/` contiene los anuncios, fotos y archivos de configuración del propietario:
  contenido ignorado por Git; solo se versionan `Data/.gitkeep` y los tres
  archivos `*.example` sin datos personales.
- `sessions/` contiene los perfiles de Firefox: contenido ignorado por Git,
  únicamente `sessions/.gitkeep` versionado.
- Variables sensibles y rutas en `.env` (plantilla en `.env.example`), nunca en código.
- Escaneo de secretos con `detect-secrets` en pre-commit.
- Logs con identificadores y fechas; se prohíbe registrar mensajes de compradores.
- Pausas configurables entre anuncios y cuentas para evitar saturación.
- Sin mecanismos de evasión de controles anti-bot. Las condiciones de servicio
  de Vinted fueron revisadas y el riesgo aceptado por el propietario.
- Revisión manual de dependencias con `pip-audit` antes de actualizar versiones.
- No se validan nombres de carpeta (decisión del propietario); la mitigación es
  el modo `--dry-run` y mensajes de error claros.
