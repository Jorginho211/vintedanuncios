from __future__ import annotations

import logging
from collections.abc import Callable

from ...shared.models import ReplyResult
from ...shared.pause import pause
from ...shared.ports import FavoriteReplier
from .command import ReplyToFavorites


def handle(
    command: ReplyToFavorites,
    *,
    replier_for: Callable[[str], FavoriteReplier],
    logger: logging.Logger,
    pause_seconds: float,
) -> ReplyResult:
    replied: list[str] = []
    errors: list[str] = []
    for account in command.accounts:
        result = replier_for(account).reply(command.template)
        for error in result.errors:
            logger.error("[%s] %s", account, error)
        for conversation_id in result.replied:
            logger.info("[%s] Respondida conversación %s", account, conversation_id)
        replied.extend(result.replied)
        errors.extend(result.errors)
        pause(pause_seconds)
    return ReplyResult(replied=tuple(replied), errors=tuple(errors))
