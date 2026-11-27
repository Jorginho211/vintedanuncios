from __future__ import annotations

from decimal import Decimal

import pytest

from vinted_anuncios.shared.offers import (
    OfferPriceError,
    format_price,
    offer_price_from_placeholder,
    parse_previous_price,
)


def test_parse_previous_price_con_coma_y_moneda() -> None:
    assert parse_previous_price("24,95 €") == Decimal("24.95")


def test_parse_previous_price_acepta_punto_y_espacios() -> None:
    assert parse_previous_price(" 9.00\u00a0€ ") == Decimal("9.00")


def test_format_price_usa_coma_y_dos_decimales() -> None:
    assert format_price(Decimal("7.5")) == "7,50"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("24,95 €", "22,95"),
        ("9,00 €", "7,00"),
        ("24.95", "22,95"),
    ],
)
def test_offer_price_from_placeholder(raw: str, expected: str) -> None:
    assert offer_price_from_placeholder(raw) == expected


@pytest.mark.parametrize("raw", ["2,00 €", "1,99 €", "abc", "", None])
def test_offer_price_rechaza_precios_invalidos(raw: str | None) -> None:
    with pytest.raises(OfferPriceError):
        offer_price_from_placeholder(raw)
