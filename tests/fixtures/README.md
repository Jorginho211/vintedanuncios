# Fixtures

- `vinted_snapshot.html`: fragmento mínimo y sin datos reales para comprobar los selectores.
- `24.95;50x60;Nike;35A.HEIC`: foto sanitizada aportada para el test de integración.
  La caption está en el **nombre del archivo**, no en sus metadatos; se lee con
  `pathlib.Path.stem`, sin librerías de metadatos.
