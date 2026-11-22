from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Caption:
    """Datos extraídos del nombre del archivo de una foto."""

    price: float
    width_cm: float
    length_cm: float
    brand: str | None
    model: str | None


@dataclass(frozen=True, slots=True)
class Listing:
    """Anuncio pendiente, ya resuelto con su título y descripción."""

    account: str
    category: str
    folder: Path
    images: tuple[Path, ...]
    caption: Caption
    title: str
    description: str


@dataclass(frozen=True, slots=True)
class ScanResult:
    listings: tuple[Listing, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PublishResult:
    ok: bool
    message: str


@dataclass(frozen=True, slots=True)
class ReplyResult:
    replied: tuple[str, ...]
    errors: tuple[str, ...]
