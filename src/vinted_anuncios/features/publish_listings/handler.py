from __future__ import annotations

import logging
from collections.abc import Callable

from ...shared.models import PublishResult
from ...shared.pause import pause
from ...shared.ports import ListingPublisher, ListingStore
from .command import PublishListings


def handle(
    command: PublishListings,
    *,
    publisher_for: Callable[[str], ListingPublisher],
    store: ListingStore,
    logger: logging.Logger,
    pause_seconds: float,
) -> tuple[PublishResult, ...]:
    results: list[PublishResult] = []
    for listing in command.listings:
        logger.info("[%s/%s] %s", listing.account, listing.category, listing.folder.name)
        outcome = publisher_for(listing.account).publish(listing)
        logger.info("%s: %s", listing.folder.name, outcome.message)
        if outcome.ok and store.delete(listing.folder):
            logger.info("Carpeta eliminada tras confirmación: %s", listing.folder)
        pause(pause_seconds)
        results.append(outcome)
    return tuple(results)
