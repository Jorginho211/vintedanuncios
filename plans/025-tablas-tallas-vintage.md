# Plan 025 — Tablas de tallas vintage (W23–W38 y ancho × largo)

**Estado:** implementado. Sustituye las tablas del plan 018.

## Objetivo

- Pantalones: tabla de equivalencia entre ancho plano en cm y tallas W23 a W38,
  con salida `WXX | ESXX` (sin espacio después de `ES`) y `ES = W + 10`.
- Tops: tabla vintage 2D explícita de ancho × largo, de `XXXS` a `XXXL`.

## Decisiones acordadas con el propietario

- El propietario pidió derivar las equivalencias; se usa la convención estándar
  `ancho_plano_cm = W × 2,54 / 2 = W × 1,27`, con cortes a media talla.
- Pantalones: W23 a W38, ambos inclusive; 28,58–48,90 cm. Fuera de rango, error.
- Tops: bandas de ancho (pecho plano) y de largo (hombro a bajo) con 9 niveles.
  `XXXS` y `XXXL` son abiertos en los extremos para no rechazar prendas vintage
  pequeñas o grandes. Fuera de 34 cm de ancho o 50 cm de largo, error.
- Matriz 9×9: el ancho determina la talla; un largo 3 o más bandas más corto
  baja la talla una posición. El largo nunca sube la talla.
- Se conserva `matches_vinted_size`: normaliza texto, así que admite tanto
  `ES42` como `ES 42` en las opciones de Vinted.

## Cambios previstos

1. `shared/sizes.py`: tablas nuevas, firma `size_for(kind, width_cm, length_cm=None)`
   (largo obligatorio para `top`) y formato `W{w} | ES{w+10}`.
2. `features/scan_listings/handler.py`: pasar `caption.length_cm`.
3. Tests: tablas, límites, matriz, escaneo y etiquetas del publicador.
4. `CONSTITUTION.md`, `docs/architecture.md`, `docs/checklist.md` y nota en el
   plan 018 sobre las tablas obsoletas.
5. Verificación: `ruff check`, `mypy`, `pytest`. Sin `--publish` ni E2E.

## Consecuencias

- La tabla anterior estaba desplazada: `42 cm` daba `W34 | ES 44`; ahora da
  `W33 | ES43`. Los W impares producen ES impar porque se mantiene `ES = W + 10`.
- Los tops dejan de usar `4XL`–`8XL`: el máximo es `XXXL`.
