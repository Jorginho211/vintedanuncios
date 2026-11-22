from __future__ import annotations

from dataclasses import dataclass

from ...shared.models import Listing


@dataclass(frozen=True, slots=True)
class PublishListings:
    """Comando: publicar los anuncios pendientes."""

    listings: tuple[Listing, ...]
