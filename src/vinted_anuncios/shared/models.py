from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Mode(StrEnum):
    """Única fuente de verdad sobre si se escribe o no en Vinted."""

    DRY_RUN = "dry-run"
    SIMULATE_SEND = "simulate-send"
    CHECK_SUBMIT = "check-submit"
    PUBLISH = "publish"


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
    config_category: str
    form_category: str
    folder: Path
    images: tuple[Path, ...]
    caption: Caption
    title: str
    description: str
    size: str


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


@dataclass(frozen=True, slots=True)
class FavoriteNotification:
    """Notificación de favorito inspeccionada, sin datos personales."""

    account: str
    url: str
    notification_id: str
    replied: bool


@dataclass(frozen=True, slots=True)
class FavoriteScanResult:
    notifications: tuple[FavoriteNotification, ...]
    stopped_reason: str
    errors: tuple[str, ...]
