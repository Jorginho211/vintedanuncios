from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class SettingsError(ValueError):
    """La configuración de entorno es inválida o está incompleta."""


@dataclass(frozen=True, slots=True)
class Settings:
    """Valores de runtime leídos una sola vez del entorno."""

    data_dir: Path
    selenium_data_dir: Path
    profiles_dir: Path
    selenium_profiles_dir: Path
    selenium_url: str
    timezone: ZoneInfo
    wait_seconds: float
    action_delay_min: float
    action_delay_max: float
    pause_between_listings: float
    pause_between_accounts: float
    log_dir: Path


def _number(env: Mapping[str, str], name: str, default: float, *, positive: bool) -> float:
    raw = env.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise SettingsError(f"{name} debe ser un número: {raw!r}") from exc
    if value < 0 or (positive and value == 0):
        limit = "mayor que 0" if positive else "0 o mayor"
        raise SettingsError(f"{name} debe ser {limit}: {raw!r}")
    return value


def _check_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SettingsError(f"SELENIUM_URL no es válida: {url!r}")
    return url


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Lee y valida las variables de entorno; ``environ`` permite inyectarlas en tests."""
    env = os.environ if environ is None else environ

    timezone_name = env.get("TIMEZONE", "Europe/Madrid")
    try:
        timezone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise SettingsError(f"TIMEZONE no es válida: {timezone_name!r}") from exc

    action_delay_min = _number(env, "SELENIUM_ACTION_DELAY_MIN", 1.0, positive=False)
    action_delay_max = _number(env, "SELENIUM_ACTION_DELAY_MAX", 2.0, positive=False)
    if action_delay_min > action_delay_max:
        raise SettingsError("SELENIUM_ACTION_DELAY_MIN no puede superar SELENIUM_ACTION_DELAY_MAX")

    return Settings(
        data_dir=Path(env.get("DATA_DIR", "Data")),
        selenium_data_dir=Path(env.get("SELENIUM_DATA_DIR", "/Data")),
        profiles_dir=Path(env.get("PROFILES_DIR", "sessions")),
        selenium_profiles_dir=Path(env.get("SELENIUM_PROFILES_DIR", "/sessions")),
        selenium_url=_check_url(env.get("SELENIUM_URL", "http://127.0.0.1:4444")),
        timezone=timezone,
        wait_seconds=_number(env, "SELENIUM_WAIT_SECONDS", 15.0, positive=True),
        action_delay_min=action_delay_min,
        action_delay_max=action_delay_max,
        pause_between_listings=_number(env, "PAUSE_BETWEEN_LISTINGS", 0.0, positive=False),
        pause_between_accounts=_number(env, "PAUSE_BETWEEN_ACCOUNTS", 0.0, positive=False),
        log_dir=Path("logs"),
    )
