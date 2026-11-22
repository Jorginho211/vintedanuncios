from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReplyToFavorites:
    """Comando: responder una vez a los avisos de favorito."""

    accounts: tuple[str, ...]
    template: str
