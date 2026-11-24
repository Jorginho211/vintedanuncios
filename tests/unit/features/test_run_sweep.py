from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from pathlib import Path

import pytest

from vinted_anuncios.adapters.filesystem import FilesystemListingStore
from vinted_anuncios.features.reply_favorites.dry_run import DryRunFavoriteReplier
from vinted_anuncios.features.run_sweep import runtime as runtime_module
from vinted_anuncios.features.run_sweep.handler import run_publish, run_reply, run_sweep
from vinted_anuncios.features.run_sweep.noop_store import NoOpListingStore
from vinted_anuncios.features.run_sweep.runtime import SeleniumRuntime
from vinted_anuncios.shared.config import ConfigError
from vinted_anuncios.shared.models import Caption, Listing, Mode, PublishResult, ReplyResult
from vinted_anuncios.shared.ports import (
    DriverPort,
    ElementPort,
    FavoriteReplier,
    ListingPublisher,
    ListingStore,
)
from vinted_anuncios.shared.settings import Settings, load_settings

IMAGE_NAME = "25;40x30;Levis;501.JPG"
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


class RecordingReplier:
    def __init__(self, result: ReplyResult) -> None:
        self.result = result
        self.templates: list[str] = []

    def reply(self, template: str) -> ReplyResult:
        self.templates.append(template)
        return self.result


class FakeRuntime:
    def __init__(
        self,
        publisher: ListingPublisher,
        store: ListingStore,
        replier: FavoriteReplier | None = None,
    ) -> None:
        self._publisher = publisher
        self._replier: FavoriteReplier = replier if replier is not None else StubReplier()
        self.store = store
        self.closed = False
        self.replier_accounts: list[str] = []
        self.released: list[str] = []

    def publisher_for(self, account: str) -> ListingPublisher:
        return self._publisher

    def replier_for(self, account: str) -> FavoriteReplier:
        self.replier_accounts.append(account)
        return self._replier

    def release(self, account: str) -> None:
        self.released.append(account)

    def close(self) -> None:
        self.closed = True


class StubVintedPublisher:
    def __init__(
        self,
        driver: DriverPort,
        settings: Settings,
        logger: logging.Logger,
        *,
        submit: bool = True,
        check_submit: bool = False,
    ) -> None:
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
        json.dumps({"Pantalones Anchos": {"size": "pants", "default": "Título"}}),
        encoding="utf-8",
    )
    (data_dir / "description.txt").write_text("Descripción", encoding="utf-8")
    (data_dir / "reply_added_favorites.txt").write_text("Gracias", encoding="utf-8")
    (folder / IMAGE_NAME).write_bytes(b"foto")
    return folder


def _prepare_accounts(tmp_path: Path, *accounts: str) -> Path:
    data_dir = tmp_path / "Data"
    data_dir.mkdir(parents=True, exist_ok=True)
    for name in accounts:
        (data_dir / name).mkdir()
    (data_dir / "reply_added_favorites.txt").write_text("Gracias", encoding="utf-8")
    return data_dir


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


def test_sweep_abre_sesion_solo_para_la_cuenta_con_anuncios_y_la_cierra(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _prepare(tmp_path)
    created: list[str] = []
    closed: list[DriverPort] = []
    _patch_factory(monkeypatch, created, closed)
    monkeypatch.setattr(runtime_module, "VintedListingPublisher", StubVintedPublisher)

    run_sweep(_settings(tmp_path), Mode.PUBLISH, logger=LOGGER)

    assert created == ["Cuenta"]
    assert len(closed) == 1


def test_publish_borra_carpeta_tras_confirmacion(tmp_path: Path) -> None:
    folder = _prepare(tmp_path)
    publisher = RecordingPublisher(PublishResult(ok=True, message="publicado"))
    runtime = FakeRuntime(publisher, FilesystemListingStore(_settings(tmp_path).data_dir))

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
    runtime = FakeRuntime(publisher, FilesystemListingStore(_settings(tmp_path).data_dir))

    run_sweep(
        _settings(tmp_path),
        Mode.PUBLISH,
        logger=LOGGER,
        runtime_factory=lambda *_args, **_kwargs: runtime,
    )

    assert (folder / IMAGE_NAME).exists()


def test_sweep_no_exige_plantilla_de_respuesta(tmp_path: Path) -> None:
    folder = _prepare(tmp_path)
    (folder.parent.parent.parent / "reply_added_favorites.txt").unlink()
    publisher = RecordingPublisher(PublishResult(ok=True, message="publicado"))
    runtime = FakeRuntime(publisher, FilesystemListingStore(_settings(tmp_path).data_dir))

    run_sweep(
        _settings(tmp_path),
        Mode.PUBLISH,
        logger=LOGGER,
        runtime_factory=lambda *_args, **_kwargs: runtime,
    )

    assert len(publisher.listings) == 1
    assert not folder.exists()


def test_sweep_no_responde_favoritos(tmp_path: Path) -> None:
    _prepare(tmp_path)
    publisher = RecordingPublisher(PublishResult(ok=True, message="publicado"))
    replier = RecordingReplier(ReplyResult((), ()))
    runtime = FakeRuntime(publisher, NoOpListingStore(), replier)

    run_sweep(
        _settings(tmp_path),
        Mode.PUBLISH,
        logger=LOGGER,
        runtime_factory=lambda *_args, **_kwargs: runtime,
    )

    assert len(publisher.listings) == 1
    assert replier.templates == []
    assert runtime.replier_accounts == []


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


def test_run_publish_no_responde_favoritos(tmp_path: Path) -> None:
    _prepare(tmp_path)
    publisher = RecordingPublisher(PublishResult(ok=True, message="publicado"))
    replier = RecordingReplier(ReplyResult((), ()))
    runtime = FakeRuntime(publisher, NoOpListingStore(), replier)

    run_publish(
        _settings(tmp_path),
        Mode.PUBLISH,
        logger=LOGGER,
        runtime_factory=lambda *_args, **_kwargs: runtime,
    )

    assert len(publisher.listings) == 1
    assert replier.templates == []
    assert runtime.closed is True


def test_run_reply_recorre_las_cuentas_desde_data(tmp_path: Path) -> None:
    data_dir = _prepare_accounts(tmp_path, "CuentaB", "CuentaA")
    replier = RecordingReplier(ReplyResult(replied=("1",), errors=()))
    runtime = FakeRuntime(
        RecordingPublisher(PublishResult(ok=True, message="publicado")),
        NoOpListingStore(),
        replier,
    )

    run_reply(
        _settings(tmp_path),
        Mode.PUBLISH,
        logger=LOGGER,
        runtime_factory=lambda *_args, **_kwargs: runtime,
    )

    assert runtime.replier_accounts == ["CuentaA", "CuentaB"]
    assert replier.templates == ["Gracias", "Gracias"]
    assert not (data_dir / "config.json").exists()
    assert not (data_dir / "description.txt").exists()
    assert runtime.closed is True


def test_run_reply_sin_cuentas_no_crea_runtime(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    _prepare_accounts(tmp_path)

    def forbidden(*_args: object, **_kwargs: object) -> FakeRuntime:
        raise AssertionError("No se debe crear el runtime sin cuentas")

    with caplog.at_level(logging.WARNING):
        run_reply(
            _settings(tmp_path),
            Mode.DRY_RUN,
            logger=LOGGER,
            runtime_factory=forbidden,
        )

    assert "No hay carpetas de cuenta" in caplog.text


def test_run_reply_sin_plantilla_falla_antes_de_crear_runtime(tmp_path: Path) -> None:
    data_dir = _prepare_accounts(tmp_path, "CuentaA")
    (data_dir / "reply_added_favorites.txt").unlink()

    def forbidden(*_args: object, **_kwargs: object) -> FakeRuntime:
        raise AssertionError("No se debe crear el runtime sin plantilla")

    with pytest.raises(ConfigError):
        run_reply(
            _settings(tmp_path),
            Mode.DRY_RUN,
            logger=LOGGER,
            runtime_factory=forbidden,
        )


def test_run_reply_sin_data_falla(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        run_reply(_settings(tmp_path), Mode.DRY_RUN, logger=LOGGER)


def test_run_reply_dry_run_no_crea_navegador(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _prepare_accounts(tmp_path, "Cuenta")
    created: list[str] = []
    closed: list[DriverPort] = []
    _patch_factory(monkeypatch, created, closed)

    run_reply(_settings(tmp_path), Mode.DRY_RUN, logger=LOGGER)

    assert created == []
    assert closed == []


def test_run_reply_publish_crea_y_cierra_driver_por_cuenta(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _prepare_accounts(tmp_path, "CuentaA", "CuentaB")
    created: list[str] = []
    closed: list[DriverPort] = []
    _patch_factory(monkeypatch, created, closed)
    monkeypatch.setattr(runtime_module, "VintedFavoriteReplier", StubVintedReplier)

    run_reply(_settings(tmp_path), Mode.PUBLISH, logger=LOGGER)

    assert created == ["CuentaA", "CuentaB"]
    assert len(closed) == 2


def test_simulate_send_no_crea_driver_hasta_que_hay_trabajo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    created: list[str] = []
    closed: list[DriverPort] = []
    _patch_factory(monkeypatch, created, closed)
    settings = _settings(tmp_path)
    runtime = SeleniumRuntime(settings, Mode.SIMULATE_SEND, ("Cuenta",), LOGGER)

    assert created == []
    assert isinstance(runtime.store, FilesystemListingStore)
    assert isinstance(runtime.replier_for("Cuenta"), DryRunFavoriteReplier)
    assert created == []
    runtime.close()


def test_simulate_send_configura_el_publicador_sin_submit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    created: list[str] = []
    closed: list[DriverPort] = []
    _patch_factory(monkeypatch, created, closed)
    captured: dict[str, bool] = {}

    class CapturePublisher:
        def __init__(
            self,
            driver: DriverPort,
            settings: Settings,
            logger: logging.Logger,
            *,
            submit: bool,
            check_submit: bool = False,
        ) -> None:
            captured["submit"] = submit
            captured["check_submit"] = check_submit

        def publish(self, listing: Listing) -> PublishResult:
            return PublishResult(ok=True, message="simulado")

    monkeypatch.setattr(runtime_module, "VintedListingPublisher", CapturePublisher)
    runtime = SeleniumRuntime(_settings(tmp_path), Mode.SIMULATE_SEND, ("Cuenta",), LOGGER)

    runtime.publisher_for("Cuenta").publish(
        Listing(
            account="Cuenta",
            config_category="Pantalones Anchos",
            form_category="Pantalones Anchos",
            folder=Path("Data/Cuenta/Pantalones Anchos/Anuncio"),
            images=(),
            caption=Caption(1.0, 1.0, 1.0, None, None),
            title="Titulo",
            description="Descripcion",
            size="W32 | ES42",
        )
    )

    assert captured["submit"] is False
    assert captured["check_submit"] is False
    assert created == ["Cuenta"]
    runtime.close()
    assert len(closed) == 1


def test_check_submit_no_publica_ni_borra_carpetas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    created: list[str] = []
    closed: list[DriverPort] = []
    _patch_factory(monkeypatch, created, closed)
    captured: dict[str, bool] = {}

    class CapturePublisher:
        def __init__(
            self,
            driver: DriverPort,
            settings: Settings,
            logger: logging.Logger,
            *,
            submit: bool,
            check_submit: bool = False,
        ) -> None:
            captured["submit"] = submit
            captured["check_submit"] = check_submit

        def publish(self, listing: Listing) -> PublishResult:
            return PublishResult(ok=True, message="diagnóstico")

    monkeypatch.setattr(runtime_module, "VintedListingPublisher", CapturePublisher)
    runtime = SeleniumRuntime(_settings(tmp_path), Mode.CHECK_SUBMIT, ("Cuenta",), LOGGER)

    assert isinstance(runtime.store, NoOpListingStore)
    runtime.publisher_for("Cuenta").publish(
        Listing(
            account="Cuenta",
            config_category="Cortavientos.CrazyJackets",
            form_category="Cortavientos",
            folder=Path("Data/Cuenta/Cortavientos.CrazyJackets/Anuncio"),
            images=(),
            caption=Caption(24.95, 62.0, 75.0, None, None),
            title="Titulo",
            description="Descripcion",
            size="XXXL",
        )
    )

    assert captured == {"submit": False, "check_submit": True}
    assert created == ["Cuenta"]
    runtime.close()
    assert len(closed) == 1
