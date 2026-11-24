from __future__ import annotations

import stat
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from vinted_anuncios.adapters.selenium_driver import SeleniumDriverFactory
from vinted_anuncios.shared.settings import Settings, load_settings


class FakeRemote:
    def __init__(self, command_executor: str, options: Options) -> None:
        self.command_executor = command_executor
        self.options = options
        self.quit_calls = 0

    def quit(self) -> None:
        self.quit_calls += 1


def settings_for(tmp_path: Path) -> Settings:
    return load_settings({"PROFILES_DIR": str(tmp_path), "SELENIUM_PROFILES_DIR": "/sessions"})


def test_create_uses_profile_in_place(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    created: list[FakeRemote] = []

    def fake_remote(command_executor: str, options: Options) -> FakeRemote:
        driver = FakeRemote(command_executor, options)
        created.append(driver)
        return driver

    monkeypatch.setattr(webdriver, "Remote", fake_remote)
    factory = SeleniumDriverFactory(settings_for(tmp_path))

    driver = factory.create("CuentaA")

    capabilities = created[0].options.to_capabilities()
    firefox_options = capabilities["moz:firefoxOptions"]
    assert firefox_options["args"] == ["-profile", "/sessions/CuentaA"]
    assert "profile" not in firefox_options
    assert created[0].command_executor == "http://127.0.0.1:4444"
    assert (tmp_path / "CuentaA").is_dir()
    assert (tmp_path / "CuentaA").stat().st_mode & stat.S_IWOTH

    factory.close(driver)
    assert created[0].quit_calls == 1


def test_create_rejects_read_only_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    profile = tmp_path / "CuentaA"
    profile.mkdir()
    profile.chmod(0o755)
    monkeypatch.setattr(
        webdriver,
        "Remote",
        lambda command_executor, options: pytest.fail("no debe crear sesión"),
    )
    factory = SeleniumDriverFactory(settings_for(tmp_path))

    with pytest.raises(PermissionError, match="no es escribible"):
        factory.create("CuentaA")
