from __future__ import annotations

import json
from pathlib import Path

from vinted_anuncios.features.scan_listings.handler import handle
from vinted_anuncios.features.scan_listings.query import ScanListings
from vinted_anuncios.shared.config import load_config
from vinted_anuncios.shared.models import ScanResult


def _prepare(tmp_path: Path, *, image_name: str | None = "25;40x30;Levis;501.JPG") -> Path:
    data_dir = tmp_path / "Data"
    folder = data_dir / "Cuenta A" / "Cortavientos.General" / "Anuncio 1"
    folder.mkdir(parents=True)
    (data_dir / "config.json").write_text(
        json.dumps(
            {
                "Cortavientos.General": {
                    "size": "top",
                    "default": "Título por defecto",
                    "levis": "Título Levis",
                }
            }
        ),
        encoding="utf-8",
    )
    (data_dir / "description.txt").write_text(
        "Descripción común, talla {{TALLA}}", encoding="utf-8"
    )
    if image_name is not None:
        (folder / image_name).write_bytes(b"foto")
    return folder


def _scan(tmp_path: Path) -> ScanResult:
    data_dir = tmp_path / "Data"
    return handle(ScanListings(data_dir=data_dir, config=load_config(data_dir)))


def test_scan_separa_categoria_de_config_y_de_formulario(tmp_path: Path) -> None:
    _prepare(tmp_path)
    result = _scan(tmp_path)
    assert result.errors == ()
    assert len(result.listings) == 1
    listing = result.listings[0]
    assert listing.account == "Cuenta A"
    assert listing.config_category == "Cortavientos.General"
    assert listing.form_category == "Cortavientos"
    assert listing.title == "Levis 501 Título Levis"
    assert listing.size == "S"
    assert listing.description == "Descripción común, talla S"
    assert listing.caption.model == "501"
    assert listing.caption.brand == "Levis"
    assert listing.caption.price == 25.0


def test_scan_sin_caption_en_el_nombre_registra_error(tmp_path: Path) -> None:
    _prepare(tmp_path, image_name="foto.JPG")
    result = _scan(tmp_path)
    assert any("caption" in error for error in result.errors)


def test_scan_prueba_siguiente_imagen_si_la_primera_no_tiene_caption(tmp_path: Path) -> None:
    folder = _prepare(tmp_path, image_name="foto.JPG")
    (folder / "20;30x40.JPG").write_bytes(b"foto")
    result = _scan(tmp_path)
    assert result.errors == ()
    assert len(result.listings) == 1
    assert result.listings[0].caption.price == 20.0


def test_scan_rechaza_heic_con_mensaje_explicito(tmp_path: Path) -> None:
    folder = _prepare(tmp_path, image_name=None)
    (folder / "25;40x30;Levis;501.HEIC").write_bytes(b"foto")
    result = _scan(tmp_path)
    assert any("HEIC" in error and "JPEG" in error for error in result.errors)


def test_scan_ignora_config_y_description(tmp_path: Path) -> None:
    _prepare(tmp_path, image_name=None)
    result = _scan(tmp_path)
    assert any("imágenes" in error for error in result.errors)


def test_scan_calcula_talla_de_pantalon_y_resuelve_el_placeholder(tmp_path: Path) -> None:
    data_dir = tmp_path / "Data"
    folder = data_dir / "Cuenta A" / "Pantalones Anchos" / "Anuncio"
    folder.mkdir(parents=True)
    (data_dir / "config.json").write_text(
        json.dumps(
            {
                "Pantalones Anchos": {
                    "size": "pants",
                    "default": "Jeans baggy",
                }
            }
        ),
        encoding="utf-8",
    )
    (data_dir / "description.txt").write_text("Talla: {{TALLA}}", encoding="utf-8")
    (folder / "25;40x30.JPG").write_bytes(b"foto")

    result = _scan(tmp_path)

    assert result.errors == ()
    assert len(result.listings) == 1
    assert result.listings[0].size == "W32 | ES 42"
    assert result.listings[0].description == "Talla: W32 | ES 42"


def test_scan_registra_error_si_la_medida_esta_fuera_de_tabla(tmp_path: Path) -> None:
    folder = _prepare(tmp_path, image_name="25;80x30.JPG")
    result = _scan(tmp_path)

    assert result.listings == ()
    assert len(result.errors) == 1
    assert str(folder) in result.errors[0]
    assert "fuera de la tabla" in result.errors[0]
