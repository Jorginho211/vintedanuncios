from __future__ import annotations

import logging
from collections.abc import Callable

from ...shared.config import load_config, load_reply_template, validate_data_dir
from ...shared.models import Mode
from ...shared.ports import Runtime
from ...shared.settings import Settings
from ..publish_listings import handler as publish_handler
from ..publish_listings.command import PublishListings
from ..reply_favorites import handler as reply_handler
from ..reply_favorites.command import ReplyToFavorites
from ..scan_listings import handler as scan_handler
from ..scan_listings.query import ScanListings, subdirectories
from .runtime import SeleniumRuntime


def run_sweep(
    settings: Settings,
    mode: Mode,
    *,
    logger: logging.Logger,
    runtime_factory: Callable[..., Runtime] = SeleniumRuntime,
) -> None:
    """Compone y ejecuta un barrido completo; valida la configuración una sola vez."""
    validate_data_dir(settings.data_dir)
    config = load_config(settings.data_dir)
    template = load_reply_template(settings.data_dir)

    result = scan_handler.handle(ScanListings(data_dir=settings.data_dir, config=config))
    for error in result.errors:
        logger.error("Error de escaneo: %s", error)

    accounts = tuple(item.name for item in subdirectories(settings.data_dir))
    runtime = runtime_factory(settings, mode, accounts, logger)
    try:
        publish_handler.handle(
            PublishListings(listings=result.listings),
            publisher_for=runtime.publisher_for,
            store=runtime.store,
            logger=logger,
            pause_seconds=settings.pause_between_listings,
        )
        reply_handler.handle(
            ReplyToFavorites(accounts=accounts, template=template),
            replier_for=runtime.replier_for,
            logger=logger,
            pause_seconds=settings.pause_between_accounts,
        )
    finally:
        runtime.close()
