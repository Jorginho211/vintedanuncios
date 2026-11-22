# Plan 006 — Publicador con Selenium

**Estado:** estructura implementada; selectores pendientes de validar en Vinted.

**Objetivo:** rellenar el formulario de publicación con los datos resueltos.

**Tareas realizadas**
- `browser.py`: driver remoto con perfil por cuenta.
- `selectors.py`: selectores centralizados y snapshot de prueba.
- `publisher.py`: relleno de título, descripción, precio, marca, modelo opcional, categoría y fotos.
- Borrado de la carpeta solo tras confirmación y con `--publish`.

**Pendiente**
- Validar los selectores reales de Vinted.
- Definir el destino del modelo.
- Comprobar la persistencia del perfil (plan 002).
