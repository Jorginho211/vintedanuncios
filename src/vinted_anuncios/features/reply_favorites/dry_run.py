from __future__ import annotations

import logging

from ...shared.models import FavoriteScanResult


class DryRunFavoriteReplier:
    """Simula la respuesta de favoritos sin navegador ni acciones."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def scan_favorites(self, template: str | None) -> FavoriteScanResult:
        self._logger.info("[dry-run] Se responderían las notificaciones de favorito")
        return FavoriteScanResult(notifications=(), stopped_reason="dry_run", errors=())
