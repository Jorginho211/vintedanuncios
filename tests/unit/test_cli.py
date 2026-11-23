from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from vinted_anuncios import cli as cli_module
from vinted_anuncios.shared.config import ConfigError
from vinted_anuncios.shared.models import Mode
from vinted_anuncios.shared.settings import load_settings

LOGGER = logging.getLogger("test-cli")


def _patch_common(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        cli_module, "load_settings", lambda: load_settings({"DATA_DIR": str(tmp_path)})
    )
    monkeypatch.setattr(cli_module, "setup_logging", lambda _dir: LOGGER)


def _recorder(name: str, calls: list[tuple[str, object]]) -> Callable[..., None]:
    def record(*args: object, **_kwargs: object) -> None:
        calls.append((name, args[1]))

    return record


def _forbidden(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("No se debe ejecutar esta acción")


def test_vinted_sin_subcomando_hace_el_barrido_completo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_common(monkeypatch, tmp_path)
    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(cli_module, "run_sweep", _recorder("sweep", calls))
    monkeypatch.setattr(cli_module, "run_publish", _forbidden)
    monkeypatch.setattr(cli_module, "run_reply", _forbidden)

    result = CliRunner().invoke(cli_module.app, [])

    assert result.exit_code == 0, result.output
    assert calls == [("sweep", Mode.DRY_RUN)]


def test_subcommand_publish_solo_publica(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_common(monkeypatch, tmp_path)
    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(cli_module, "run_publish", _recorder("publish", calls))
    monkeypatch.setattr(cli_module, "run_reply", _forbidden)
    monkeypatch.setattr(cli_module, "run_sweep", _forbidden)

    result = CliRunner().invoke(cli_module.app, ["publish", "--publish"])

    assert result.exit_code == 0, result.output
    assert calls == [("publish", Mode.PUBLISH)]


def test_subcommand_reply_solo_responde(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_common(monkeypatch, tmp_path)
    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(cli_module, "run_reply", _recorder("reply", calls))
    monkeypatch.setattr(cli_module, "run_publish", _forbidden)
    monkeypatch.setattr(cli_module, "run_sweep", _forbidden)

    result = CliRunner().invoke(cli_module.app, ["reply", "--dry-run"])

    assert result.exit_code == 0, result.output
    assert calls == [("reply", Mode.DRY_RUN)]


def test_subcommand_sweep_respeta_la_precedencia_de_dry_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_common(monkeypatch, tmp_path)
    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(cli_module, "run_sweep", _recorder("sweep", calls))

    result = CliRunner().invoke(cli_module.app, ["sweep", "--publish", "--dry-run"])

    assert result.exit_code == 0, result.output
    assert calls == [("sweep", Mode.DRY_RUN)]


def test_schedule_arranca_el_scheduler_con_los_dos_jobs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_common(monkeypatch, tmp_path)
    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(cli_module, "start", _recorder("start", calls))
    monkeypatch.setattr(cli_module, "run_sweep", _forbidden)

    result = CliRunner().invoke(cli_module.app, ["sweep", "--schedule"])

    assert result.exit_code == 0, result.output
    assert calls == [("start", Mode.DRY_RUN)]


def test_error_de_configuracion_termina_con_codigo_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_common(monkeypatch, tmp_path)

    def raise_config_error(*_args: object, **_kwargs: object) -> None:
        raise ConfigError("Falta la plantilla")

    monkeypatch.setattr(cli_module, "run_reply", raise_config_error)

    result = CliRunner().invoke(cli_module.app, ["reply"])

    assert result.exit_code == 1
    assert "Error: Falta la plantilla" in result.output
