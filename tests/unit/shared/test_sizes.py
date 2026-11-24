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
        (28.58, "W23 | ES33"),
        (29.84, "W23 | ES33"),
        (29.85, "W24 | ES34"),
        (34.29, "W27 | ES37"),
        (35.56, "W28 | ES38"),
        (40.01, "W32 | ES42"),
        (42.0, "W33 | ES43"),
        (48.89, "W38 | ES48"),
    ],
)
def test_tabla_de_pantalones(width_cm: float, expected: str) -> None:
    assert size_for("pants", width_cm) == expected


@pytest.mark.parametrize(
    ("width_cm", "length_cm", "expected"),
    [
        (34.0, 50.0, "XXXS"),
        (36.99, 54.99, "XXXS"),
        (37.0, 55.0, "XXS"),
        (45.0, 70.0, "S"),
        (47.0, 70.0, "M"),
        (51.0, 70.0, "L"),
        (45.0, 50.0, "XS"),
        (60.0, 90.0, "XXXL"),
    ],
)
def test_matriz_de_ropa_superior(width_cm: float, length_cm: float, expected: str) -> None:
    assert size_for("top", width_cm, length_cm) == expected


@pytest.mark.parametrize(
    ("kind", "width_cm", "length_cm"),
    [
        ("pants", 28.57, None),
        ("pants", 48.90, None),
        ("top", 33.99, 70.0),
        ("top", 45.0, 49.99),
    ],
)
def test_medida_fuera_de_tabla_es_error(
    kind: str, width_cm: float, length_cm: float | None
) -> None:
    with pytest.raises(SizeError, match="fuera de la tabla"):
        size_for(kind, width_cm, length_cm)


def test_top_sin_largo_es_error() -> None:
    with pytest.raises(SizeError, match="Falta el largo"):
        size_for("top", 45.0)


def test_tipo_de_talla_desconocido() -> None:
    with pytest.raises(SizeError, match="desconocido"):
        size_for("shorts", 40.0, 70.0)


@pytest.mark.parametrize(
    ("option", "expected"),
    [
        ("W32", True),
        ("ES42", True),
        ("ES 42", True),
        ("W32 / ES42", True),
        ("talla 42", False),
        ("W30", False),
    ],
)
def test_opciones_de_vinted_para_talla_de_pantalon(option: str, expected: bool) -> None:
    assert matches_vinted_size("W32 | ES42", option) is expected


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
