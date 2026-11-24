# Plan 026 — Diagnóstico del botón «Subir» y de la talla de los tops

## Estado

Implementado y verificado en modo seguro (sin `--publish`).

## Motivo

Con los anuncios de prueba, el cortavientos `62x75` calcula `XXXL` y no se
selecciona en el formulario; el clic en «Subir» acaba en `TimeoutException`
incluso cuando el botón se ve activo. Los dos pantalones (`W30 | ES40` y
`W27 | ES37`) sirven de control.

## Decisiones acordadas con el propietario

- Diagnóstico primero: añadir marcas de paso y detalle de error antes de
  corregir la lógica.
- Modo de diagnóstico **sin publicar**, mutuamente excluyente con los demás
  modos: rellena el formulario, comprueba el estado del botón y descarta los
  cambios. No borra carpetas de anuncio.
- Si Vinted no ofrece la talla calculada, se falla sin publicar: no se inventan
  equivalencias (`XXXL` no se cambia por `3XL` salvo decisión nueva).
- Sin `--publish`: la evidencia del clic real solo se recogerá con autorización
  explícita.

## Evidencia recogida

- El cortavientos usa `data-testid="category-size-single-grid_chips-input"` y
  `..._chips-content`; los pantalones usan `category-size-single-grid-input` y
  `category-size-single-grid-content`. El desplegable del cortavientos sí ofrece
  `XXXL` con `aria-label="XXXL"` y `role="checkbox"`.
- El campo `input#size` mantiene `value=""` incluso después de elegir talla, así
  que la confirmación se apoya en `aria-checked="true"`; si no hay ninguna señal,
  se avisa en el log pero no se bloquea la publicación.
- En los dos pantalones el diagnóstico llega hasta «Subir» con el botón activo
  (`disabled` ausente) y las tallas visibles (`W30 | ES 40`, `W27 | ES 36`).
  Por tanto el timeout de «Subir» no parece fallo de clic, sino de la navegación
  posterior; queda pendiente de una prueba real autorizada.

## Cambios implementados

1. `adapters/vinted_publisher.py`: pasos finos en `_choose_size()` y
   `_submit_form()`; mensajes de error con selector, estado del botón, URL y
   opciones de talla encontradas; verificación de talla por `aria-checked`;
   modo diagnóstico que para antes de pulsar «Subir».
2. `adapters/selectors.py`: selectores de talla válidos para las dos variantes
   del DOM (`-input`/`_chips-input` y `-content`/`_chips-content`).
3. `shared/models.py`, `cli.py`, `features/run_sweep/`: modo `--check-submit`,
   bandera mutuamente excluyente, runtime sin borrado de carpetas y reply
   simulado en diagnóstico.
4. `tests/unit/`, fixture y `REAL_SELECTORS`: cobertura de mensajes, modo,
   selección por `aria-label`/`aria-checked` y no equivalencia `3XL`/`XXXL`.
5. `docs/checklist.md`, `docs/architecture.md` y `CONSTITUTION.md`.

## Verificación

- `ruff check .`, `ruff format .`, `mypy src tests` y `pytest` en verde.
- `vinted --dry-run` con los anuncios de prueba: sin errores.
- `publish --check-submit` sobre una copia de `Data/` y del perfil: los tres
  anuncios llegan hasta «Subir» con el botón activo; el cortavientos selecciona
  `XXXL` tras corregir el selector. Sin publicar ni borrar carpetas.
- `publish --simulate-send` sobre la copia: los tres anuncios terminan
  simulados; el tercero falló una vez por timeout al desplazar el listado de
  marcas y pasó al repetirlo. `Data/` original conserva sus tres carpetas.
- Pendiente: solo con autorización explícita, una prueba real de `--publish`
  para confirmar la navegación tras «Subir»; el mensaje de error ya distingue
  clic fallido de falta de navegación e incluye errores visibles de Vinted.
