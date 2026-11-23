from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from vinted_anuncios.adapters.selectors import HOME_URL
from vinted_anuncios.features.check_session.command import CheckSession, SessionError
from vinted_anuncios.features.check_session.handler import check_session
from vinted_anuncios.shared.ports import DriverPort, ElementPort
from vinted_anuncios.shared.settings import Settings, load_settings


class FakeDriver:
    def __init__(self) -> None:
        self.urls: list[str] = []
        self.quit_calls = 0

    def get(self, url: str) -> None:
        self.urls.append(url)

    def find_element(self, by: str, value: str) -> ElementPort:
        raise NotImplementedError

    def find_elements(self, by: str, value: str) -> Sequence[ElementPort]:
        return ()

    def quit(self) -> None:
        self.quit_calls += 1


class FakeFactory:
    def __init__(self, driver: FakeDriver) -> None:
        self.driver = driver
        self.created: list[str] = []
        self.closed = 0

    def create(self, account: str) -> DriverPort:
        self.created.append(account)
        return self.driver

    def close(self, driver: DriverPort) -> None:
        self.closed += 1
        driver.quit()


def make_settings(tmp_path: Path) -> Settings:
    (tmp_path / "CuentaA").mkdir()
    return load_settings({"PROFILES_DIR": str(tmp_path)})


def test_check_session_opens_home_and_closes(tmp_path: Path) -> None:
    driver = FakeDriver()
    factory = FakeFactory(driver)
    confirmed: list[bool] = []

    check_session(
        CheckSession("CuentaA"),
        make_settings(tmp_path),
        factory,
        lambda: confirmed.append(True),
    )

    assert driver.urls == [HOME_URL]
    assert factory.created == ["CuentaA"]
    assert confirmed == [True]
    assert factory.closed == 1
    assert driver.quit_calls == 1


def test_check_session_closes_if_confirmation_fails(tmp_path: Path) -> None:
    driver = FakeDriver()
    factory = FakeFactory(driver)

    def fail() -> None:
        raise RuntimeError("teclado")

    with pytest.raises(RuntimeError, match="teclado"):
        check_session(CheckSession("CuentaA"), make_settings(tmp_path), factory, fail)

    assert factory.closed == 1
    assert driver.quit_calls == 1


@pytest.mark.parametrize("name", ["", ".", "..", "CuentaA/Otra", "/CuentaA"])
def test_check_session_rejects_invalid_names(tmp_path: Path, name: str) -> None:
    factory = FakeFactory(FakeDriver())

    with pytest.raises(SessionError, match="no válido"):
        check_session(CheckSession(name), make_settings(tmp_path), factory, lambda: None)

    assert factory.created == []


def test_check_session_rejects_missing_folder(tmp_path: Path) -> None:
    settings = load_settings({"PROFILES_DIR": str(tmp_path)})
    factory = FakeFactory(FakeDriver())

    with pytest.raises(SessionError, match="No existe la carpeta de sesión"):
        check_session(CheckSession("CuentaA"), settings, factory, lambda: None)

    assert factory.created == []
