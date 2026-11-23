from __future__ import annotations

import logging
from collections.abc import Callable

from ...shared.models import Listing, PublishResult
from ...shared.pause import pause
from ...shared.ports import ListingPublisher, ListingStore
from .command import PublishListings


def handle(
    command: PublishListings,
    *,
    publisher_for: Callable[[str], ListingPublisher],
    store: ListingStore,
    release: Callable[[str], None],
    logger: logging.Logger,
    pause_seconds: float,
) -> tuple[PublishResult, ...]:
    """Publica agrupando por cuenta y libera su sesión al terminar la cuenta."""
    results: list[PublishResult] = []
    by_account: dict[str, list[Listing]] = {}
    for listing in command.listings:
        by_account.setdefault(listing.account, []).append(listing)

    for account, listings in by_account.items():
        try:
            for listing in listings:
                logger.info(
                    "[%s/%s] %s", listing.account, listing.config_category, listing.folder.name
                )
                outcome = publisher_for(account).publish(listing)
                logger.info("%s: %s", listing.folder.name, outcome.message)
                if outcome.ok and store.delete(listing.folder):
                    logger.info("Carpeta eliminada tras la publicación: %s", listing.folder)
                pause(pause_seconds)
                results.append(outcome)
        finally:
            release(account)
    return tuple(results)
