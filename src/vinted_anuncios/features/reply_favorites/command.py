from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScanFavoriteNotifications:
    """Comando: inspeccionar avisos de favorito sin responder."""

    accounts: tuple[str, ...]
