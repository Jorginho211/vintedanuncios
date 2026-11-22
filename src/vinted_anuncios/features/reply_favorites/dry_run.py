from __future__ import annotations

import logging

from ...shared.models import ReplyResult


class DryRunFavoriteReplier:
    """Simula la revisión de favoritos sin navegador ni envío de mensajes."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def reply(self, template: str) -> ReplyResult:
        self._logger.info("[dry-run] Se revisarían los avisos de favorito")
        return ReplyResult(replied=(), errors=())
