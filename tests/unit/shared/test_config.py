from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinted_anuncios.shared.config import (
    ConfigError,
    load_config,
    load_reply_template,
    title_for,
    validate_data_dir,
)

DATA_DIR = Path(__file__).resolve().parents[3] / "Data"


def test_load_config_lee_archivos_reales() -> None:
    config = load_config(DATA_DIR)
    assert "Pantalones Anchos" in config.categories
    assert config.description.strip()


def test_title_for_usa_variante_de_marca() -> None:
    config = load_config(DATA_DIR)
    assert (
        title_for(config, "Pantalones Anchos", "Levis")
        == config.categories["Pantalones Anchos"]["levis"]
    )
    assert (
        title_for(config, "Pantalones Anchos", "Nike")
        == config.categories["Pantalones Anchos"]["default"]
    )
    assert title_for(config, "Cortavientos.General", None).startswith("Track Jacket")


def test_title_for_categoria_desconocida() -> None:
    config = load_config(DATA_DIR)
    with pytest.raises(ConfigError):
        title_for(config, "Inexistente", None)


def test_load_config_rechaza_json_invalido(tmp_path: Path) -> None:
    (tmp_path / "config.json").write_text("{ no es json", encoding="utf-8")
    (tmp_path / "description.txt").write_text("texto", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(tmp_path)


def test_load_reply_template_sin_archivo(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_reply_template(tmp_path)


def test_load_reply_template_vacio(tmp_path: Path) -> None:
    (tmp_path / "reply_added_favorites.txt").write_text("  \n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_reply_template(tmp_path)


def test_load_reply_template_con_archivo(tmp_path: Path) -> None:
    (tmp_path / "reply_added_favorites.txt").write_text(
        "  Gracias por tu interés  \n", encoding="utf-8"
    )
    assert load_reply_template(tmp_path) == "Gracias por tu interés"


def test_config_json_mantiene_las_ocho_categorias() -> None:
    raw = json.loads((DATA_DIR / "config.json").read_text(encoding="utf-8"))
    assert len(raw) == 8


def test_validate_data_dir_con_archivos_reales() -> None:
    validate_data_dir(DATA_DIR)


def test_validate_data_dir_sin_archivos(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="config.json.example"):
        validate_data_dir(tmp_path)


def test_archivos_ejemplo_existen() -> None:
    for name in (
        "config.json.example",
        "description.example",
        "reply_added_favorites.example",
    ):
        assert (DATA_DIR / name).is_file()
