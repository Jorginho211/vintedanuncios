from __future__ import annotations

import logging
from collections.abc import Callable

from ...shared.models import FavoriteNotification, FavoriteScanResult
from ...shared.pause import pause
from ...shared.ports import FavoriteReplier
from .command import ScanFavoriteNotifications


def handle(
    command: ScanFavoriteNotifications,
    *,
    replier_for: Callable[[str], FavoriteReplier],
    logger: logging.Logger,
    pause_seconds: float,
    release: Callable[[str], None] = lambda _account: None,
) -> FavoriteScanResult:
    notifications: list[FavoriteNotification] = []
    errors: list[str] = []
    stopped_reason = "no_accounts"
    for index, account in enumerate(command.accounts):
        try:
            result = replier_for(account).scan_favorites()
            for error in result.errors:
                logger.error("[%s] %s", account, error)
            for notice in result.notifications:
                state = "respondida" if notice.replied else "pendiente"
                logger.info(
                    "[%s] Favorito %s %s (%s)",
                    account,
                    notice.notification_id,
                    state,
                    notice.url,
                )
            notifications.extend(result.notifications)
            errors.extend(result.errors)
            stopped_reason = result.stopped_reason
            if index < len(command.accounts) - 1:
                pause(pause_seconds)
        finally:
            release(account)
    return FavoriteScanResult(
        notifications=tuple(notifications),
        stopped_reason=stopped_reason,
        errors=tuple(errors),
    )
