from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinted_anuncios.shared.config import (
    ConfigError,
    load_config,
    load_reply_template,
    size_kind_for,
    title_for,
    validate_data_dir,
    validate_reply_data_dir,
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


def test_size_kind_for_lee_la_clave_reservada() -> None:
    config = load_config(DATA_DIR)
    assert size_kind_for(config, "Pantalones Anchos") == "pants"
    assert size_kind_for(config, "Cortavientos.General") == "top"


def test_load_config_exige_clave_size_valida(tmp_path: Path) -> None:
    (tmp_path / "description.txt").write_text("texto", encoding="utf-8")
    (tmp_path / "config.json").write_text(
        json.dumps({"Pantalones": {"default": "Título"}}), encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="'size'"):
        load_config(tmp_path)

    (tmp_path / "config.json").write_text(
        json.dumps({"Pantalones": {"size": "shorts", "default": "Título"}}),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="'size'"):
        load_config(tmp_path)


def test_title_for_ignora_la_clave_size() -> None:
    config = load_config(DATA_DIR)
    assert title_for(config, "Pantalones Anchos", "Size").startswith("Y2K")


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


def test_validate_data_dir_no_exige_plantilla_de_respuesta(tmp_path: Path) -> None:
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "description.txt").write_text("texto", encoding="utf-8")

    validate_data_dir(tmp_path)


def test_validate_reply_data_dir_acepta_arbol_de_cuentas(tmp_path: Path) -> None:
    (tmp_path / "CuentaA").mkdir()
    validate_reply_data_dir(tmp_path)


def test_validate_reply_data_dir_sin_directorio(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="No existe el directorio"):
        validate_reply_data_dir(tmp_path / "Inexistente")


def test_archivos_ejemplo_existen() -> None:
    for name in (
        "config.json.example",
        "description.txt.example",
        "reply_added_favorites.txt.example",
    ):
        assert (DATA_DIR / name).is_file()
