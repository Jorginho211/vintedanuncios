# Estrategia de testing

## Niveles

- **Unitarios** (`tests/unit/`): `shared/` (settings, caption, títulos, lock,
  cálculo de ofertas y contratos) y `features/` (query de escaneo, publicación y
  respuesta de favoritos). Los tests de `run_sweep`, `run_publish` y `run_reply`
  inyectan un runtime falso: sin navegador ni red. `run_sweep` equivale a
  `run_publish` y no revisa favoritos; `run_reply` exige la plantilla en modos
  reales y pasa el flag de escritura al adapter. El adapter del reply se prueba
  con un driver y elementos falsos que comprueban el orden de las acciones sin
  escribir en Vinted. La CLI se prueba con `CliRunner` y el scheduler con un
  scheduler falso; tampoco abren Selenium.
- **Integración** (`tests/integration/`): lectura real de la caption desde el
  nombre de una foto y comprobación de selectores contra un snapshot HTML.
- **E2E:** no automatizado. La verificación contra Vinted se hace con
  `docs/checklist.md` en modo `--dry-run` y, puntualmente, con `--publish`.
  El cambio de precio y el envío del mensaje del reply solo se pueden confirmar
  en Vinted con `--publish` autorizado; los tests unitarios cubren la lógica y
  el orden de llamadas con fakes.

## Cobertura

Objetivo: **80 %** sobre la lógica pura (`settings`, `config`, `metadata`,
`models`, `ports` y los handlers de `features/`). Los adapters de Selenium, el
runtime, el scheduler y la CLI quedan excluidos de la medición.

## Fixtures

- `tests/fixtures/vinted_snapshot.html`: fragmento HTML mínimo con los atributos
  que usan los selectores. Sin datos reales.
- `24.95;50x60;Nike;35A.HEIC`: foto sanitizada cuyo nombre contiene la caption.
  El test de integración la usa sin leer metadatos del archivo.

## Ejecución

```bash
poetry run pytest
poetry run ruff check .
poetry run mypy src tests
```

El pre-commit ejecuta Ruff, mypy y detección de secretos. Los tests se ejecutan
bajo demanda, no en cada commit.
