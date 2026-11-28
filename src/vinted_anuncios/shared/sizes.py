from __future__ import annotations

import re
from typing import Literal

SizeKind = Literal["pants", "top"]

SIZE_KINDS: frozenset[str] = frozenset({"pants", "top"})

# Pantalones: (mínimo, máximo exclusivo, W), con ancho plano en centímetros.
# Cada W equivale a 2,54 cm de cintura, es decir 1,27 cm de ancho plano.
_PANTS_RANGES: tuple[tuple[float, float, int], ...] = (
    (28.58, 29.85, 23),
    (29.85, 31.12, 24),
    (31.12, 32.39, 25),
    (32.39, 33.66, 26),
    (33.66, 34.93, 27),
    (34.93, 36.20, 28),
    (36.20, 37.47, 29),
    (37.47, 38.74, 30),
    (38.74, 40.01, 31),
    (40.01, 41.28, 32),
    (41.28, 42.55, 33),
    (42.55, 43.82, 34),
    (43.82, 45.09, 35),
    (45.09, 46.36, 36),
    (47.63, 48.90, 38),
)

# Tops vintage: bandas de ancho (pecho plano) y de largo (hombro a bajo).
# Los extremos quedan abiertos porque las tallas vintage no son uniformes.
_TOP_WIDTH_BANDS: tuple[tuple[float, float], ...] = (
    (34.0, 37.0),
    (37.0, 40.0),
    (40.0, 43.0),
    (43.0, 46.0),
    (46.0, 49.0),
    (49.0, 52.0),
    (52.0, 55.0),
    (55.0, 58.0),
    (58.0, float("inf")),
)
_TOP_LENGTH_BANDS: tuple[tuple[float, float], ...] = (
    (50.0, 55.0),
    (55.0, 59.0),
    (59.0, 63.0),
    (63.0, 67.0),
    (67.0, 71.0),
    (71.0, 75.0),
    (75.0, 79.0),
    (79.0, 83.0),
    (83.0, float("inf")),
)

# Matriz explícita: filas = banda de largo, columnas = banda de ancho.
# El ancho manda; un largo tres bandas o más más corto baja una talla.
_TOP_MATRIX: tuple[tuple[str, ...], ...] = (
    ("XXXS", "XXS", "XS", "XS", "S", "M", "L", "XL", "XXL"),
    ("XXXS", "XXS", "XS", "S", "S", "M", "L", "XL", "XXL"),
    ("XXXS", "XXS", "XS", "S", "M", "M", "L", "XL", "XXL"),
    ("XXXS", "XXS", "XS", "S", "M", "L", "L", "XL", "XXL"),
    ("XXXS", "XXS", "XS", "S", "M", "L", "XL", "XL", "XXL"),
    ("XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXL"),
    ("XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"),
    ("XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"),
    ("XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"),
)

_NON_ALNUM_RE = re.compile(r"[^\w]+", re.UNICODE)


class SizeError(ValueError):
    """La medida no permite calcular una talla con las tablas acordadas."""


def _band_index(bands: tuple[tuple[float, float], ...], value: float, axis: str) -> int:
    """Devuelve la banda que contiene la medida, con extremo máximo excluido."""
    for index, (minimum, maximum) in enumerate(bands):
        if minimum <= value < maximum:
            return index
    minimum = bands[0][0]
    raise SizeError(
        f"Medida {value:g} cm de {axis} fuera de la tabla de top (mínimo {minimum:g} cm)"
    )


def size_for(kind: str, width_cm: float, length_cm: float | None = None) -> str:
    """Devuelve la talla para una prenda medida en centímetros.

    Los rangos son intervalos ``[mínimo, máximo)``; una medida fuera de la
    tabla es un error y nunca se redondea al extremo más cercano. Los tops
    necesitan también el largo porque usan una matriz ancho × largo.
    """
    if kind == "pants":
        for minimum, maximum, waist in _PANTS_RANGES:
            if minimum <= width_cm < maximum:
                return f"W{waist} | ES{waist + 10}"
        raise SizeError(
            f"Medida {width_cm:g} cm fuera de la tabla de pants "
            f"({_PANTS_RANGES[0][0]:g}–{_PANTS_RANGES[-1][1]:g} cm)"
        )

    if kind == "top":
        if length_cm is None:
            raise SizeError("Falta el largo para calcular la talla de top")
        width_index = _band_index(_TOP_WIDTH_BANDS, width_cm, "ancho")
        length_index = _band_index(_TOP_LENGTH_BANDS, length_cm, "largo")
        return _TOP_MATRIX[length_index][width_index]

    raise SizeError(f"Tipo de talla desconocido: {kind!r}")


def _normalize(value: str) -> str:
    """Deja `W32 | ES42` como `w32es42` para comparar opciones de Vinted."""
    return _NON_ALNUM_RE.sub("", value.casefold())


def matches_vinted_size(size: str, option_text: str) -> bool:
    """Comprueba si una opción del desplegable representa la talla calculada.

    Para tallas con dos formatos (``W32`` y ``ES42``) se admite que la opción
    contenga cualquiera de los dos. Para tallas de una sola etiqueta (``M``,
    ``XXL``) se exige coincidencia exacta para no confundirlas con otras palabras.
    """
    candidates = tuple(normalized for part in size.split("|") if (normalized := _normalize(part)))
    option = _normalize(option_text)
    if option in candidates:
        return True
    return len(candidates) > 1 and any(candidate in option for candidate in candidates)
