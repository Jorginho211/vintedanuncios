from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from pathlib import Path

import pytest

from vinted_anuncios.adapters.filesystem import FilesystemListingStore
from vinted_anuncios.features.run_sweep import runtime as runtime_module
from vinted_anuncios.features.run_sweep.handler import run_sweep
from vinted_anuncios.features.run_sweep.noop_store import NoOpListingStore
from vinted_anuncios.shared.config import ConfigError
from vinted_anuncios.shared.models import Listing, Mode, PublishResult, ReplyResult
from vinted_anuncios.shared.ports import (
    DriverPort,
    ElementPort,
    FavoriteReplier,
    ListingPublisher,
    ListingStore,
)
from vinted_anuncios.shared.settings import Settings, load_settings

IMAGE_NAME = "25;40x30;Levis.HEIC"
LOGGER = logging.getLogger("test")


class FakeDriver:
    def get(self, url: str) -> None:
        pass

    def find_element(self, by: str, value: str) -> ElementPort:
        raise NotImplementedError

    def find_elements(self, by: str, value: str) -> Sequence[ElementPort]:
        return ()

    def quit(self) -> None:
        pass


class RecordingPublisher:
    def __init__(self, result: PublishResult) -> None:
        self.result = result
        self.listings: list[Listing] = []

    def publish(self, listing: Listing) -> PublishResult:
        self.listings.append(listing)
        return self.result


class StubReplier:
    def reply(self, template: str) -> ReplyResult:
        return ReplyResult((), ())


class FakeRuntime:
    def __init__(self, publisher: ListingPublisher, store: ListingStore) -> None:
        self._publisher = publisher
        self._replier: FavoriteReplier = StubReplier()
        self.store = store
        self.closed = False

    def publisher_for(self, account: str) -> ListingPublisher:
        return self._publisher

    def replier_for(self, account: str) -> FavoriteReplier:
        return self._replier

    def close(self) -> None:
        self.closed = True


class StubVintedPublisher:
    def __init__(self, driver: DriverPort, settings: Settings, logger: logging.Logger) -> None:
        pass

    def publish(self, listing: Listing) -> PublishResult:
        return PublishResult(ok=True, message="publicado")


class StubVintedReplier:
    def __init__(self, driver: DriverPort, settings: Settings, logger: logging.Logger) -> None:
        pass

    def reply(self, template: str) -> ReplyResult:
        return ReplyResult((), ())


def _settings(tmp_path: Path) -> Settings:
    return load_settings(
        {
            "DATA_DIR": str(tmp_path / "Data"),
            "PROFILES_DIR": str(tmp_path / "sessions"),
        }
    )


def _prepare(tmp_path: Path) -> Path:
    data_dir = tmp_path / "Data"
    folder = data_dir / "Cuenta" / "Pantalones Anchos" / "Anuncio"
    folder.mkdir(parents=True)
    (data_dir / "config.json").write_text(
        json.dumps({"Pantalones Anchos": {"default": "Título"}}), encoding="utf-8"
    )
    (data_dir / "description.txt").write_text("Descripción", encoding="utf-8")
    (data_dir / "reply_added_favorites.txt").write_text("Gracias", encoding="utf-8")
    (folder / IMAGE_NAME).write_bytes(b"foto")
    return folder


def _patch_factory(
    monkeypatch: pytest.MonkeyPatch, created: list[str], closed: list[DriverPort]
) -> None:
    class Recorder:
        def __init__(self, settings: Settings) -> None:
            pass

        def create(self, account: str) -> DriverPort:
            created.append(account)
            return FakeDriver()

        def close(self, driver: DriverPort) -> None:
            closed.append(driver)

    monkeypatch.setattr(runtime_module, "SeleniumDriverFactory", Recorder)


def test_dry_run_no_crea_navegador_ni_borra(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = _prepare(tmp_path)
    created: list[str] = []
    closed: list[DriverPort] = []
    _patch_factory(monkeypatch, created, closed)

    run_sweep(_settings(tmp_path), Mode.DRY_RUN, logger=LOGGER)

    assert created == []
    assert closed == []
    assert (folder / IMAGE_NAME).exists()


def test_publish_crea_driver_y_lo_cierra(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _prepare(tmp_path)
    created: list[str] = []
    closed: list[DriverPort] = []
    _patch_factory(monkeypatch, created, closed)
    monkeypatch.setattr(runtime_module, "VintedListingPublisher", StubVintedPublisher)
    monkeypatch.setattr(runtime_module, "VintedFavoriteReplier", StubVintedReplier)

    run_sweep(_settings(tmp_path), Mode.PUBLISH, logger=LOGGER)

    assert created == ["Cuenta"]
    assert len(closed) == 1


def test_publish_borra_carpeta_tras_confirmacion(tmp_path: Path) -> None:
    folder = _prepare(tmp_path)
    publisher = RecordingPublisher(PublishResult(ok=True, message="publicado"))
    runtime = FakeRuntime(publisher, FilesystemListingStore())

    run_sweep(
        _settings(tmp_path),
        Mode.PUBLISH,
        logger=LOGGER,
        runtime_factory=lambda *_args, **_kwargs: runtime,
    )

    assert len(publisher.listings) == 1
    assert runtime.closed is True
    assert not folder.exists()


def test_confirmacion_fallida_no_borra_carpeta(tmp_path: Path) -> None:
    folder = _prepare(tmp_path)
    publisher = RecordingPublisher(PublishResult(ok=False, message="fallo"))
    runtime = FakeRuntime(publisher, FilesystemListingStore())

    run_sweep(
        _settings(tmp_path),
        Mode.PUBLISH,
        logger=LOGGER,
        runtime_factory=lambda *_args, **_kwargs: runtime,
    )

    assert (folder / IMAGE_NAME).exists()


def test_falta_plantilla_aborta_antes_de_publicar(tmp_path: Path) -> None:
    folder = _prepare(tmp_path)
    (folder.parent.parent.parent / "reply_added_favorites.txt").unlink()

    def forbidden(*_args: object, **_kwargs: object) -> FakeRuntime:
        raise AssertionError("No se debe crear el runtime si falta configuración")

    with pytest.raises(ConfigError):
        run_sweep(
            _settings(tmp_path),
            Mode.PUBLISH,
            logger=LOGGER,
            runtime_factory=forbidden,
        )
    assert (folder / IMAGE_NAME).exists()


def test_simulacion_no_borra_con_store_inerte(tmp_path: Path) -> None:
    folder = _prepare(tmp_path)
    publisher = RecordingPublisher(PublishResult(ok=True, message="[dry-run]"))
    runtime = FakeRuntime(publisher, NoOpListingStore())

    run_sweep(
        _settings(tmp_path),
        Mode.DRY_RUN,
        logger=LOGGER,
        runtime_factory=lambda *_args, **_kwargs: runtime,
    )

    assert (folder / IMAGE_NAME).exists()
