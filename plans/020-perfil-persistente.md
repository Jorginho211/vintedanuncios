# Plan 020 — Perfil Firefox persistente en el volumen montado

**Estado:** implementado; pendiente la verificación manual del criterio 1.

**Objetivo:** que el login de Vinted realizado en el Firefox del grid sobreviva al cierre
del driver y a nuevas ejecuciones. Cierra el spike pendiente del plan 002.

## Diagnóstico

`SeleniumDriverFactory` asigna `options.profile = "sessions/<Cuenta>"`. Selenium 4
clona ese directorio, lo comprime en base64 y lo envía en
`moz:firefoxOptions.profile`; geckodriver lo descomprime en
`/tmp/rust_mozprofile...` dentro del contenedor y lo borra al cerrar la sesión.
Los logs del grid confirman `moz:profile=/tmp/rust_mozprofileasbIn5`. El volumen
`./sessions:/sessions:rw` no se usa: `sessions/<Cuenta>` es solo una plantilla.

## Decisión acordada

Usar el perfil **in situ** del volumen montado mediante el argumento de Firefox
`-profile /sessions/<Cuenta>`, con `moz:profile` de geckodriver apuntando a esa
ruta. No se exportan cookies ni se copia el perfil de vuelta.

## Cambios por fase

### Fase 1 — Configuración
- `Settings.selenium_profiles_dir` desde `SELENIUM_PROFILES_DIR` (default `/sessions`),
  análogo a `SELENIUM_DATA_DIR`.
- `.env.example`, `README.md`, `docs/architecture.md`, `CONSTITUTION.md` y planes.

### Fase 2 — Adapter
- `SeleniumDriverFactory.create()` deja de usar `options.profile` y pasa el
  argumento `-profile`. No se fija `--marionette-port`: geckodriver 0.31.0 ya
  lee `MarionetteActivePort` del perfil y evita colisiones entre sesiones.
- Comprueba que la carpeta existe y es escribible por el usuario del contenedor.
- Sin Selenium en `shared/`.

### Fase 3 — Pruebas y verificación
- Tests unitarios de las capabilities generadas (ruta del perfil, sin ZIP y sin
  puerto fijo: geckodriver lee `MarionetteActivePort` del perfil).
- `ruff`, `mypy`, `pytest` en verde.
- Verificación manual con `docs/checklist.md`: login en `check-session CuentaA`,
  Enter, repetir y comprobar que sigue iniciada. Sin E2E automático contra Vinted.

## Criterios de aceptación

- Dos sesiones consecutivas con la misma cuenta conservan el login.
- Ninguna sesión usa `/tmp/rust_mozprofile...` como perfil efectivo.
- `vinted --dry-run` sigue sin crear drivers.
- Sin cambios en el contenido versionado de `sessions/`.

## Resultado

- `ruff check`, `ruff format --check`, `mypy src tests` y `pytest` en verde:
  139 tests, 98 % de cobertura sobre la lógica pura medida.
- `vinted --dry-run` sigue terminando con código 0 y sin crear drivers.
- Tests nuevos: `tests/unit/adapters/test_selenium_driver.py` comprueba que las
  capabilities llevan `args == ["-profile", "/sessions/CuentaA"]`, que no se envía
  `profile` (ZIP), que la carpeta se crea escribible y que se rechaza una carpeta
  sin permiso de escritura.
- `SE_NODE_SESSION_TIMEOUT` sube a 7200 para no perder la sesión durante el login
  manual por VNC; comprobado en `/status` (`sessionTimeout: 7200000`).
- Prueba local contra el grid, sin Vinted ni `sessions/`: al abrir una sesión con
  `-profile /tmp/prueba-perfil`, `moz:profile` devuelve esa ruta (no un
  `/tmp/rust_mozprofile...`) y el directorio conserva 40 archivos tras `quit()`.
- Sin E2E contra Vinted y sin tocar el contenido de `sessions/`. La verificación
  con dos sesiones consecutivas queda pendiente de ejecutar por el propietario
  siguiendo `docs/checklist.md`.
