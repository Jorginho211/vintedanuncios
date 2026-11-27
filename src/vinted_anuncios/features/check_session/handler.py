from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from ...adapters.selectors import HOME_URL
from ...shared.ports import DriverFactory
from ...shared.selenium_lock import selenium_lock
from ...shared.settings import Settings
from .command import CheckSession, SessionError


def check_session(
    command: CheckSession,
    settings: Settings,
    factory: DriverFactory,
    confirm: Callable[[], None],
    url: str = HOME_URL,
) -> None:
    """Abre Vinted con el perfil indicado y espera a que el usuario lo cierre."""
    name = command.session
    if not name or name in {".", ".."} or Path(name).name != name:
        raise SessionError(f"Nombre de sesión no válido: {name!r}")

    profile = settings.profiles_dir / name
    if not profile.is_dir():
        raise SessionError(f"No existe la carpeta de sesión {profile}")

    with selenium_lock(settings, logging.getLogger("vinted_anuncios.check_session")):
        driver = factory.create(name)
        try:
            driver.get(url)
            confirm()
        finally:
            factory.close(driver)
