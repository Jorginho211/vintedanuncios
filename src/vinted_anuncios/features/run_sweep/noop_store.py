from __future__ import annotations

from pathlib import Path


class NoOpListingStore:
    """No borra nada: se usa en simulación."""

    def delete(self, folder: Path) -> bool:
        return False
