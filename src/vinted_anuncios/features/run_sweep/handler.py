from __future__ import annotations

import logging
from collections.abc import Callable

from ...shared.config import load_config, validate_data_dir, validate_reply_data_dir
from ...shared.models import Mode, ScanResult
from ...shared.ports import Runtime
from ...shared.selenium_lock import selenium_lock
from ...shared.settings import Settings
from ..publish_listings import handler as publish_handler
from ..publish_listings.command import PublishListings
from ..reply_favorites import handler as reply_handler
from ..reply_favorites.command import ScanFavoriteNotifications
from ..scan_listings import handler as scan_handler
from ..scan_listings.query import ScanListings, subdirectories
from .runtime import SeleniumRuntime

RuntimeFactory = Callable[..., Runtime]


def _accounts(settings: Settings) -> tuple[str, ...]:
    return tuple(item.name for item in subdirectories(settings.data_dir))


def _publish(
    runtime: Runtime, result: ScanResult, settings: Settings, logger: logging.Logger
) -> None:
    publish_handler.handle(
        PublishListings(listings=result.listings),
        publisher_for=runtime.publisher_for,
        store=runtime.store,
        release=runtime.release,
        logger=logger,
        pause_seconds=settings.pause_between_listings,
    )


def _reply(
    runtime: Runtime,
    accounts: tuple[str, ...],
    settings: Settings,
    logger: logging.Logger,
) -> None:
    result = reply_handler.handle(
        ScanFavoriteNotifications(accounts=accounts),
        replier_for=runtime.replier_for,
        logger=logger,
        pause_seconds=settings.pause_between_accounts,
        release=runtime.release,
    )
    logger.info(
        "Inspección de favoritos completada: %s notificaciones, motivo=%s, errores=%s",
        len(result.notifications),
        result.stopped_reason,
        len(result.errors),
    )


def run_publish(
    settings: Settings,
    mode: Mode,
    *,
    logger: logging.Logger,
    runtime_factory: RuntimeFactory = SeleniumRuntime,
) -> None:
    """Escanea ``Data`` y publica anuncios; no revisa favoritos."""
    validate_data_dir(settings.data_dir)
    config = load_config(settings.data_dir)
    result = scan_handler.handle(ScanListings(data_dir=settings.data_dir, config=config))
    for error in result.errors:
        logger.error("Error de escaneo: %s", error)

    accounts = _accounts(settings)
    if mode is Mode.DRY_RUN:
        runtime = runtime_factory(settings, mode, accounts, logger)
        try:
            _publish(runtime, result, settings, logger)
        finally:
            runtime.close()
        return

    with selenium_lock(settings, logger):
        runtime = runtime_factory(settings, mode, accounts, logger)
        try:
            _publish(runtime, result, settings, logger)
        finally:
            runtime.close()


def run_reply(
    settings: Settings,
    mode: Mode,
    *,
    logger: logging.Logger,
    runtime_factory: RuntimeFactory = SeleniumRuntime,
) -> None:
    """Inspecciona favoritos en cada cuenta; no envía respuestas ni publica anuncios."""
    validate_reply_data_dir(settings.data_dir)
    accounts = _accounts(settings)
    if not accounts:
        logger.warning(
            "No hay carpetas de cuenta en %s; no se inspeccionan favoritos", settings.data_dir
        )
        return

    if mode is Mode.DRY_RUN:
        runtime = runtime_factory(settings, mode, accounts, logger)
        try:
            _reply(runtime, accounts, settings, logger)
        finally:
            runtime.close()
        return

    with selenium_lock(settings, logger):
        runtime = runtime_factory(settings, mode, accounts, logger)
        try:
            _reply(runtime, accounts, settings, logger)
        finally:
            runtime.close()


def run_sweep(
    settings: Settings,
    mode: Mode,
    *,
    logger: logging.Logger,
    runtime_factory: RuntimeFactory = SeleniumRuntime,
) -> None:
    """Alias de ``run_publish``: escanea ``Data`` y publica; no revisa favoritos."""
    run_publish(settings, mode, logger=logger, runtime_factory=runtime_factory)
