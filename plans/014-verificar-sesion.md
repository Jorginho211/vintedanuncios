# Plan 014 — Comando para verificar una sesión manualmente

**Estado:** completado.

**Objetivo:** añadir un comando que abra `https://www.vinted.es` con el perfil Firefox
guardado en `sessions/<sesion>` para que el propietario compruebe visualmente si
sigue iniciada la sesión. No se detecta el login de forma automática.

**Decisiones acordadas con el propietario**
1. Sintaxis: subcomando `vinted check-session <sesion>` manteniendo intacto
   `vinted --dry-run` mediante un callback de Typer con `invoke_without_command=True`.
2. Navegador: se reutiliza `SeleniumDriverFactory` (Firefox remoto del grid). Se observa
   por VNC en `http://127.0.0.1:7900` y se cierra con `quit()` al pulsar Enter.
3. Si no existe `sessions/<sesion>`, el comando termina con error claro y código 1;
   nunca crea un perfil nuevo por un nombre mal escrito.

## Cambios por fase

### Fase 1 — Caso de uso
- `features/check_session/command.py`: `CheckSession` y `SessionError`.
- `features/check_session/handler.py`: valida el nombre y la existencia de la carpeta,
  crea el driver con el factory inyectado, navega al home, espera la confirmación y
  cierra el driver en `finally`. Sin importar Selenium.
- `adapters/selectors.py`: nueva constante `HOME_URL`.

### Fase 2 — CLI
- `cli.py`: callback con `invoke_without_command=True` para preservar el barrido actual
  y subcomando `check-session` que inyecta `Settings`, `SeleniumDriverFactory` y la
  espera de Enter. Errores de sesión/configuración → mensaje en español y código 1.

### Fase 3 — Pruebas y documentación
- Tests unitarios del handler con driver y factory falsos: navegación, cierre siempre,
  nombres inválidos y carpeta ausente. Sin E2E contra Vinted.
- `README.md`, `docs/architecture.md` y `docs/checklist.md` actualizados.

## Criterios de aceptación
- `poetry run ruff check .`, `poetry run ruff format .`, `poetry run mypy src tests` y
  `poetry run pytest` en verde.
- `poetry run vinted --dry-run` conserva su comportamiento actual.
- `poetry run vinted check-session CuentaA` abre el home de Vinted en el Firefox del
  grid, permite verlo en VNC y cierra el driver al pulsar Enter.
- Un nombre inexistente o con rutas termina con código 1 y no crea carpetas.
- Sin `--publish`, sin E2E automático y sin tocar el contenido de `sessions/`.

## Resultado

- `ruff check`, `ruff format --check`, `mypy src tests` y `pytest` en verde:
  55 tests, 97 % de cobertura sobre la lógica pura medida.
- `vinted --help` muestra el subcomando y `vinted --dry-run` sigue terminando con
  código 0 y sin crear drivers.
- `vinted check-session NoExiste` y `vinted check-session ../CuentaA` terminan con
  código 1 y mensaje claro, sin crear carpetas ni contactar con Selenium.
- Sin cambios en `sessions/`, sin ejecución de `--publish` y sin E2E contra Vinted.
