# Estrategia de testing

## Niveles

- **Unitarios** (`tests/unit/`): parseo de caption, medidas, selección de título,
  carga de configuración y recorrido del árbol. Sin navegador ni red.
- **Integración** (`tests/integration/`): lectura real de la caption desde el
  nombre de una foto y comprobación de selectores contra un snapshot HTML.
- **E2E:** no automatizado. La verificación contra Vinted se hace con
  `docs/checklist.md` en modo `--dry-run` y, puntualmente, con `--publish`.

## Cobertura

Objetivo: **80 %** sobre la lógica pura (`config`, `metadata`, `models`,
`scanner`). Los módulos de Selenium quedan excluidos de la medición.

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
