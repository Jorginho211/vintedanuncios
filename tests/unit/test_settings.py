from __future__ import annotations

from pathlib import Path

import pytest

from vinted_anuncios.shared.settings import SettingsError, load_settings


def test_load_settings_usa_los_defaults() -> None:
    settings = load_settings({})
    assert settings.data_dir == Path("Data")
    assert settings.profiles_dir == Path("sessions")
    assert settings.selenium_url == "http://127.0.0.1:4444"
    assert str(settings.timezone) == "Europe/Madrid"
    assert settings.reply_cron == "*/15 * * * *"
    assert settings.wait_seconds == 15.0
    assert settings.pause_between_listings == 0.0
    assert settings.pause_between_accounts == 0.0
    assert settings.log_dir == Path("logs")


def test_load_settings_lee_los_nombres_ingleses() -> None:
    settings = load_settings(
        {
            "DATA_DIR": "/tmp/datos",
            "PROFILES_DIR": "/tmp/perfiles",
            "SELENIUM_URL": "http://127.0.0.1:5555",
            "SELENIUM_WAIT_SECONDS": "7",
            "PAUSE_BETWEEN_LISTINGS": "2",
            "PAUSE_BETWEEN_ACCOUNTS": "5",
            "TIMEZONE": "UTC",
            "REPLY_CRON": "*/5 * * * *",
        }
    )
    assert settings.data_dir == Path("/tmp/datos")
    assert settings.profiles_dir == Path("/tmp/perfiles")
    assert settings.selenium_url == "http://127.0.0.1:5555"
    assert settings.wait_seconds == 7.0
    assert settings.pause_between_listings == 2.0
    assert settings.pause_between_accounts == 5.0
    assert str(settings.timezone) == "UTC"
    assert settings.reply_cron == "*/5 * * * *"


def test_load_settings_ignora_tz() -> None:
    settings = load_settings({"TZ": "UTC"})
    assert str(settings.timezone) == "Europe/Madrid"


@pytest.mark.parametrize(
    "environ",
    [
        {"SELENIUM_WAIT_SECONDS": "0"},
        {"SELENIUM_WAIT_SECONDS": "abc"},
        {"PAUSE_BETWEEN_LISTINGS": "-1"},
        {"PAUSE_BETWEEN_ACCOUNTS": "lento"},
        {"TIMEZONE": "Zona/Que/No/Existe"},
        {"SELENIUM_URL": "ftp://127.0.0.1:4444"},
        {"REPLY_CRON": "   "},
    ],
)
def test_load_settings_rechaza_valores_invalidos(environ: dict[str, str]) -> None:
    with pytest.raises(SettingsError):
        load_settings(environ)
