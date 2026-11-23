from __future__ import annotations

import pytest

from vinted_anuncios.shared.sizes import (
    SizeError,
    matches_vinted_size,
    size_for,
)


@pytest.mark.parametrize(
    ("width_cm", "expected"),
    [
        (34.29, "W28 | ES 38"),
        (35.56, "W28 | ES 38"),
        (36.83, "W30 | ES 40"),
        (39.37, "W32 | ES 42"),
        (40.0, "W32 | ES 42"),
        (58.0, "W46 | ES 56"),
        (59.69, "W48 | ES 58"),
        (62.22, "W48 | ES 58"),
    ],
)
def test_tabla_de_pantalones(width_cm: float, expected: str) -> None:
    assert size_for("pants", width_cm) == expected


@pytest.mark.parametrize(
    ("width_cm", "expected"),
    [
        (30.0, "XXXS"),
        (32.99, "XXXS"),
        (33.0, "XXS"),
        (42.0, "M"),
        (44.0, "L"),
        (68.0, "8XL"),
        (71.99, "8XL"),
    ],
)
def test_tabla_de_ropa_superior(width_cm: float, expected: str) -> None:
    assert size_for("top", width_cm) == expected


@pytest.mark.parametrize(
    ("kind", "width_cm"),
    [
        ("pants", 34.28),
        ("pants", 62.23),
        ("top", 29.99),
        ("top", 72.0),
    ],
)
def test_medida_fuera_de_tabla_es_error(kind: str, width_cm: float) -> None:
    with pytest.raises(SizeError, match="fuera de la tabla"):
        size_for(kind, width_cm)


def test_tipo_de_talla_desconocido() -> None:
    with pytest.raises(SizeError, match="desconocido"):
        size_for("shorts", 40.0)


@pytest.mark.parametrize(
    ("option", "expected"),
    [
        ("W32", True),
        ("ES 42", True),
        ("W32 / ES42", True),
        ("talla 42", False),
        ("W30", False),
    ],
)
def test_opciones_de_vinted_para_talla_de_pantalon(option: str, expected: bool) -> None:
    assert matches_vinted_size("W32 | ES 42", option) is expected


@pytest.mark.parametrize(
    ("size", "option", "expected"),
    [
        ("M", "M", True),
        ("M", "m", True),
        ("M", "Mujer", False),
        ("M", "L", False),
        ("XXL", "XXL", True),
        ("XXL", "XL", False),
    ],
)
def test_opciones_de_vinted_para_talla_superior(size: str, option: str, expected: bool) -> None:
    assert matches_vinted_size(size, option) is expected
