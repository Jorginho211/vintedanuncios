from __future__ import annotations

import stat
from typing import cast

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from ..shared.ports import DriverFactory, DriverPort
from ..shared.settings import Settings


class SeleniumDriverFactory:
    """Crea y cierra un driver remoto con un perfil persistente por cuenta."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _prepare_profile(self, account: str) -> None:
        profile_dir = self._settings.profiles_dir / account
        if not profile_dir.exists():
            profile_dir.mkdir(parents=True)
            # Firefox corre como seluser (1200:1201) dentro del contenedor.
            profile_dir.chmod(0o777)
        elif not profile_dir.stat().st_mode & stat.S_IWOTH:
            raise PermissionError(f"El perfil {profile_dir} no es escribible por el grid")

    def create(self, account: str) -> DriverPort:
        self._prepare_profile(account)
        options = Options()
        # `options.profile` comprime el perfil y geckodriver lo despliega en
        # /tmp/rust_mozprofile..., que se borra al cerrar la sesión: el login no
        # sobreviviría. Con -profile se usa in situ el volumen /sessions montado.
        options.add_argument("-profile")
        options.add_argument(str(self._settings.selenium_profiles_dir / account))
        return cast(
            DriverPort,
            webdriver.Remote(command_executor=self._settings.selenium_url, options=options),
        )

    def close(self, driver: DriverPort) -> None:
        driver.quit()


__all__ = ["DriverFactory", "SeleniumDriverFactory"]
