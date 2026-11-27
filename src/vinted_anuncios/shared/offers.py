"""Cálculo del precio de la oferta de favoritos, sin Selenium ni configuración."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

DISCOUNT = Decimal("2.00")
CENT = Decimal("0.01")

_PRICE_PATTERN = re.compile(r"^(\d+(?:[.,]\d{1,2})?)\s*(?:€|EUR)?$")


class OfferPriceError(ValueError):
    """El precio anterior de la conversación no permite calcular la oferta."""


def parse_previous_price(raw: str | None) -> Decimal:
    """Convierte el placeholder `24,95 €` en un `Decimal` con dos decimales."""
    if not raw:
        raise OfferPriceError("El campo de oferta no tiene placeholder de precio")
    match = _PRICE_PATTERN.fullmatch(raw.strip())
    if match is None:
        raise OfferPriceError(f"No se pudo leer el precio anterior de {raw!r}")
    try:
        price = Decimal(match.group(1).replace(",", "."))
    except InvalidOperation as exc:
        raise OfferPriceError(f"No se pudo leer el precio anterior de {raw!r}") from exc
    if price <= DISCOUNT:
        raise OfferPriceError(f"El precio anterior {raw!r} no permite ofrecer 2 € menos")
    return price.quantize(CENT)


def format_price(price: Decimal) -> str:
    """Formatea un precio con coma decimal y dos decimales, sin moneda."""
    return f"{price.quantize(CENT):.2f}".replace(".", ",")


def offer_price_from_placeholder(raw: str | None) -> str:
    """Devuelve el precio a ofrecer, 2 € por debajo del precio del placeholder."""
    return format_price(parse_previous_price(raw) - DISCOUNT)
