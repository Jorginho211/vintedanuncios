from __future__ import annotations

import re
from pathlib import Path

from .models import Caption

_MEASURES_RE = re.compile(r"^(\d+(?:[.,]\d+)?)\s*[xX]\s*(\d+(?:[.,]\d+)?)$")


class CaptionError(ValueError):
    """La caption no cumple el contrato precio;medidas;marca;modelo."""


def _parse_number(value: str, field: str) -> float:
    try:
        return float(value.replace(",", "."))
    except ValueError as exc:
        raise CaptionError(f"{field} no es numérico: {value!r}") from exc


def parse_caption(raw: str) -> Caption:
    """Convierte `24.95;50x60;Nike;35A` en un ``Caption`` validado."""
    fields = [field.strip() for field in raw.split(";")]
    while fields and fields[-1] == "":
        fields.pop()

    if len(fields) < 2:
        raise CaptionError("La caption necesita al menos precio;medidas")
    if len(fields) > 4:
        raise CaptionError("La caption tiene más de 4 campos separados por ';'")

    price = _parse_number(fields[0], "precio")
    match = _MEASURES_RE.match(fields[1])
    if match is None:
        raise CaptionError(f"Medidas con formato incorrecto: {fields[1]!r} (esperado 50x60)")

    width = _parse_number(match.group(1), "ancho")
    length = _parse_number(match.group(2), "largo")
    brand = fields[2] if len(fields) > 2 and fields[2] else None
    model = fields[3] if len(fields) > 3 and fields[3] else None
    return Caption(price=price, width_cm=width, length_cm=length, brand=brand, model=model)


def caption_from_filename(path: Path) -> str:
    """Devuelve el nombre del archivo sin extensión, que es la caption."""
    return path.stem


def parse_caption_from_filename(path: Path) -> Caption:
    """Parsea directamente la caption contenida en el nombre del archivo."""
    return parse_caption(caption_from_filename(path))
