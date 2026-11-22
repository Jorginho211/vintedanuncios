from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from vinted_anuncios import browser, logging_conf, publisher, replier, runner
from vinted_anuncios.config import ConfigError
from vinted_anuncios.models import PublishResult, ReplyResult

IMAGE_NAME = "25;40x30;Levis.HEIC"


def _prepare(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_dir = tmp_path / "Data"
    folder = data_dir / "Cuenta" / "Pantalones Anchos" / "Anuncio"
    folder.mkdir(parents=True)
    (data_dir / "config.json").write_text(
        json.dumps({"Pantalones Anchos": {"default": "Título"}}), encoding="utf-8"
    )
    (data_dir / "description.txt").write_text("Descripción", encoding="utf-8")
    (data_dir / "reply_added_favorites.txt").write_text("Gracias", encoding="utf-8")
    (folder / IMAGE_NAME).write_bytes(b"foto")

    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("PROFILES_DIR", str(tmp_path / "sessions"))
    monkeypatch.setattr(logging_conf, "setup_logging", lambda: logging.getLogger("test"))
    return folder


def test_dry_run_no_crea_navegador_ni_borra(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = _prepare(tmp_path, monkeypatch)

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("--dry-run no debe crear un navegador")

    monkeypatch.setattr(browser, "create_driver", forbidden)
    runner.run_once(publish=False)
    assert (folder / IMAGE_NAME).exists()


def test_publish_crea_navegador_y_borra_tras_confirmacion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = _prepare(tmp_path, monkeypatch)
    created: list[object] = []

    def fake_create_driver(_profile: Path) -> object:
        driver = object()
        created.append(driver)
        return driver

    monkeypatch.setattr(browser, "create_driver", fake_create_driver)
    monkeypatch.setattr(browser, "close_driver", lambda _driver: None)
    monkeypatch.setattr(
        publisher,
        "publish_listing",
        lambda *_args, **_kwargs: PublishResult(ok=True, message="publicado"),
    )
    monkeypatch.setattr(
        replier,
        "reply_to_favorites",
        lambda *_args, **_kwargs: ReplyResult(replied=(), errors=()),
    )

    runner.run_once(publish=True)
    assert len(created) == 1
    assert not folder.exists()


def test_falta_plantilla_aborta_antes_de_publicar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = _prepare(tmp_path, monkeypatch)
    (tmp_path / "Data" / "reply_added_favorites.txt").unlink()

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("No se debe crear un navegador si falta configuración")

    monkeypatch.setattr(browser, "create_driver", forbidden)
    with pytest.raises(ConfigError):
        runner.run_once(publish=True)
    assert (folder / IMAGE_NAME).exists()
