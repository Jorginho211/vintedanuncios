from __future__ import annotations

import json
from pathlib import Path

from vinted_anuncios.config import load_config
from vinted_anuncios.scanner import scan


def _prepare(tmp_path: Path, *, image_name: str | None = "25;40x30;Levis;501.HEIC") -> Path:
    data_dir = tmp_path / "Data"
    folder = data_dir / "Cuenta A" / "Pantalones Anchos" / "Anuncio 1"
    folder.mkdir(parents=True)
    (data_dir / "config.json").write_text(
        json.dumps(
            {"Pantalones Anchos": {"default": "Título por defecto", "levis": "Título Levis"}}
        ),
        encoding="utf-8",
    )
    (data_dir / "description.txt").write_text("Descripción común", encoding="utf-8")
    if image_name is not None:
        (folder / image_name).write_bytes(b"foto")
    return folder


def test_scan_construye_listing_desde_el_nombre_del_archivo(tmp_path: Path) -> None:
    folder = _prepare(tmp_path)
    result = scan(tmp_path / "Data", load_config(tmp_path / "Data"))
    assert result.errors == ()
    assert len(result.listings) == 1
    listing = result.listings[0]
    assert listing.account == "Cuenta A"
    assert listing.category == "Pantalones Anchos"
    assert listing.title == "Título Levis"
    assert listing.description == "Descripción común"
    assert listing.caption.model == "501"
    assert listing.folder == folder


def test_scan_ignora_config_y_description(tmp_path: Path) -> None:
    _prepare(tmp_path, image_name=None)
    result = scan(tmp_path / "Data", load_config(tmp_path / "Data"))
    assert any("imágenes" in error for error in result.errors)


def test_scan_sin_caption_en_el_nombre_registra_error(tmp_path: Path) -> None:
    _prepare(tmp_path, image_name="foto.HEIC")
    result = scan(tmp_path / "Data", load_config(tmp_path / "Data"))
    assert any("caption" in error for error in result.errors)


def test_scan_prueba_siguiente_imagen_si_la_primera_no_tiene_caption(tmp_path: Path) -> None:
    folder = _prepare(tmp_path, image_name="foto.HEIC")
    (folder / "20;30x40.HEIC").write_bytes(b"foto")
    result = scan(tmp_path / "Data", load_config(tmp_path / "Data"))
    assert result.errors == ()
    assert len(result.listings) == 1
    assert result.listings[0].caption.price == 20.0
