from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScanFavoriteNotifications:
    """Comando: responder a los avisos de favorito aún no contestados."""

    accounts: tuple[str, ...]
    template: str | None = None
