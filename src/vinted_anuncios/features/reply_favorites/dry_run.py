from __future__ import annotations

import logging

from ...shared.models import FavoriteScanResult, ReplyResult


class DryRunFavoriteReplier:
    """Simula la inspección de favoritos sin navegador ni acciones."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def scan_favorites(self) -> FavoriteScanResult:
        self._logger.info("[dry-run] Se inspeccionarían las notificaciones de favorito")
        return FavoriteScanResult(notifications=(), stopped_reason="dry_run", errors=())

    def reply(self, template: str) -> ReplyResult:
        self._logger.info("[dry-run] Se omite el envío de respuestas en esta fase")
        return ReplyResult(replied=(), errors=())
