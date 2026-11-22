from __future__ import annotations

import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webdriver import WebDriver


def selenium_url() -> str:
    return os.getenv("SELENIUM_URL", "http://127.0.0.1:4444")


def create_driver(profile_dir: Path) -> WebDriver:
    """Crea un driver remoto usando un perfil de Firefox por cuenta."""
    profile_dir.mkdir(parents=True, exist_ok=True)
    options = Options()
    # Selenium 4 envía el directorio del perfil comprimido al nodo del grid.
    # La firma de `Options.profile` cambia entre versiones de Selenium 4;
    # asignar por nombre evita depender de la anotación del getter o del setter.
    setattr(options, "profile", str(profile_dir))  # noqa: B010
    return webdriver.Remote(command_executor=selenium_url(), options=options)


def close_driver(driver: WebDriver) -> None:
    driver.quit()
