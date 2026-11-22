from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

from selenium.webdriver.remote.webdriver import WebDriver

from . import browser, logging_conf, publisher, replier
from .config import ConfigError, load_config, load_reply_template, validate_data_dir
from .scanner import scan


def _data_dir() -> Path:
    return Path(os.getenv("DATA_DIR", "Data"))


def _profiles_dir() -> Path:
    return Path(os.getenv("PROFILES_DIR", "sessions"))


def _account_names(data_dir: Path) -> list[str]:
    return sorted(
        item.name for item in data_dir.iterdir() if item.is_dir() and not item.name.startswith(".")
    )


def _pause(env_name: str) -> None:
    try:
        seconds = float(os.getenv(env_name, "0"))
    except ValueError:
        return
    if seconds > 0:
        time.sleep(seconds)


def run_once(*, publish: bool) -> None:
    """Ejecuta un barrido completo. Sin ``publish`` solo simula."""
    logger = logging_conf.setup_logging()
    data_dir = _data_dir()
    dry_run = not publish

    try:
        validate_data_dir(data_dir)
        config = load_config(data_dir)
        template = load_reply_template(data_dir)
    except ConfigError as exc:
        logger.error("Configuración inválida: %s", exc)
        raise

    result = scan(data_dir, config)
    for error in result.errors:
        logger.error("Error de escaneo: %s", error)

    accounts = _account_names(data_dir)
    drivers: dict[str, WebDriver] = {}
    try:
        # En simulación no se abre ningún navegador: basta con validar y mostrar.
        if publish:
            for account in accounts:
                drivers[account] = browser.create_driver(_profiles_dir() / account)

        for listing in result.listings:
            logger.info("[%s/%s] %s", listing.account, listing.category, listing.folder.name)
            outcome = publisher.publish_listing(
                drivers.get(listing.account), listing, dry_run=dry_run, logger=logger
            )
            logger.info("%s: %s", listing.folder.name, outcome.message)
            if outcome.ok and publish:
                shutil.rmtree(listing.folder)
                logger.info("Carpeta eliminada tras confirmación: %s", listing.folder)
            _pause("PAUSA_ENTRE_ANUNCIOS")

        for account in accounts:
            replies = replier.reply_to_favorites(
                drivers.get(account), template, dry_run=dry_run, logger=logger
            )
            for error in replies.errors:
                logger.error("[%s] %s", account, error)
            for conversation_id in replies.replied:
                logger.info("[%s] Respondida conversación %s", account, conversation_id)
            _pause("PAUSA_ENTRE_CUENTAS")
    finally:
        for driver in drivers.values():
            browser.close_driver(driver)
