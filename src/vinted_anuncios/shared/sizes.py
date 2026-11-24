from __future__ import annotations

import re
from typing import Literal

SizeKind = Literal["pants", "top"]

SIZE_KINDS: frozenset[str] = frozenset({"pants", "top"})

# Límites superiores de cada rango, medidos sobre el ancho plano en centímetros.
# Pantalones: cada W ocupa 2,54 cm de ancho plano (2 pulgadas de cintura).
_PANTS_RANGES: tuple[tuple[float, int], ...] = (
    (29.00, 23),
    (36.83, 28),
    (39.37, 30),
    (41.91, 32),
    (44.45, 34),
    (46.99, 36),
    (49.53, 38),
    (52.07, 40),
    (54.61, 42),
    (57.15, 44),
    (59.69, 46),
    (62.23, 48),
)
_PANTS_MIN_CM = 29.00

_TOP_RANGES: tuple[tuple[float, str], ...] = (
    (33.0, "XXXS"),
    (35.0, "XXS"),
    (38.0, "XS"),
    (41.0, "S"),
    (44.0, "M"),
    (47.0, "L"),
    (50.0, "XL"),
    (53.0, "XXL"),
    (56.0, "XXXL"),
    (59.0, "4XL"),
    (62.0, "5XL"),
    (65.0, "6XL"),
    (68.0, "7XL"),
    (72.0, "8XL"),
)
_TOP_MIN_CM = 30.0

_NON_ALNUM_RE = re.compile(r"[^\w]+", re.UNICODE)


class SizeError(ValueError):
    """La medida no permite calcular una talla con las tablas acordadas."""


def size_for(kind: str, width_cm: float) -> str:
    """Devuelve la talla para un ancho plano en centímetros.

    Los rangos son intervalos ``[mínimo, máximo)``; una medida fuera de la
    tabla es un error y nunca se redondea al extremo más cercano.
    """
    ranges: tuple[tuple[float, int | str], ...]
    minimum: float
    if kind == "pants":
        ranges = _PANTS_RANGES
        minimum = _PANTS_MIN_CM
    elif kind == "top":
        ranges = _TOP_RANGES
        minimum = _TOP_MIN_CM
    else:
        raise SizeError(f"Tipo de talla desconocido: {kind!r}")

    if width_cm < minimum or width_cm >= ranges[-1][0]:
        raise SizeError(
            f"Medida {width_cm:g} cm fuera de la tabla de {kind} "
            f"({minimum:g}–{ranges[-1][0]:g} cm)"
        )

    for upper, value in ranges:
        if width_cm < upper:
            if isinstance(value, int):
                return f"W{value} | ES {value + 10}"
            return value
    raise SizeError(f"Medida {width_cm:g} cm no encaja en la tabla de {kind}")


def _normalize(value: str) -> str:
    """Deja `W32 | ES 42` como `w32es42` para comparar opciones de Vinted."""
    return _NON_ALNUM_RE.sub("", value.casefold())


def matches_vinted_size(size: str, option_text: str) -> bool:
    """Comprueba si una opción del desplegable representa la talla calculada.

    Para tallas con dos formatos (``W32`` y ``ES 42``) se admite que la opción
    contenga cualquiera de los dos. Para tallas de una sola etiqueta (``M``,
    ``XXL``) se exige coincidencia exacta para no confundirlas con otras palabras.
    """
    candidates = tuple(normalized for part in size.split("|") if (normalized := _normalize(part)))
    option = _normalize(option_text)
    if option in candidates:
        return True
    return len(candidates) > 1 and any(candidate in option for candidate in candidates)
