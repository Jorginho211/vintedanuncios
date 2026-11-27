from __future__ import annotations

import fcntl
import logging
from collections.abc import Iterator
from contextlib import contextmanager

from .settings import Settings

LOCK_FILE_NAME = ".selenium.lock"


@contextmanager
def selenium_lock(settings: Settings, logger: logging.Logger) -> Iterator[None]:
    """Serializa el uso de Selenium entre procesos con un lock de fichero."""

    lock_path = settings.profiles_dir / LOCK_FILE_NAME
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Esperando lock de Selenium: %s", lock_path)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        logger.info("Lock de Selenium adquirido")
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            logger.info("Lock de Selenium liberado")
