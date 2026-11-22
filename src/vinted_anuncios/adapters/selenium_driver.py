from __future__ import annotations

from typing import cast

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from ..shared.ports import DriverFactory, DriverPort
from ..shared.settings import Settings


class SeleniumDriverFactory:
    """Crea y cierra un driver remoto con un perfil por cuenta."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create(self, account: str) -> DriverPort:
        profile_dir = self._settings.profiles_dir / account
        profile_dir.mkdir(parents=True, exist_ok=True)
        options = Options()
        # Selenium 4 envía el directorio del perfil comprimido al nodo del grid.
        # La firma de `Options.profile` cambia entre versiones de Selenium 4;
        # asignar por nombre evita depender de la anotación del getter o del setter.
        setattr(options, "profile", str(profile_dir))  # noqa: B010
        return cast(
            DriverPort,
            webdriver.Remote(command_executor=self._settings.selenium_url, options=options),
        )

    def close(self, driver: DriverPort) -> None:
        driver.quit()


__all__ = ["DriverFactory", "SeleniumDriverFactory"]
