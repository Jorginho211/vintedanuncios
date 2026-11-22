from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """La configuración del proyecto es inválida o está incompleta."""


# Archivo obligatorio -> plantilla que se debe copiar para crearlo.
REQUIRED_FILES = {
    "config.json": "config.json.example",
    "description.txt": "description.example",
    "reply_added_favorites.txt": "reply_added_favorites.example",
}


def validate_data_dir(data_dir: Path) -> None:
    """Impide trabajar si falta alguno de los archivos de configuración."""
    missing = [name for name in REQUIRED_FILES if not (data_dir / name).is_file()]
    if missing:
        details = ", ".join(f"{name} (copia {data_dir / REQUIRED_FILES[name]})" for name in missing)
        raise ConfigError(f"Faltan archivos obligatorios en {data_dir}: {details}")


@dataclass(frozen=True, slots=True)
class Config:
    categories: dict[str, dict[str, str]]
    description: str


def load_config(data_dir: Path) -> Config:
    """Carga ``config.json`` y ``description.txt`` desde ``data_dir``."""
    config_path = data_dir / "config.json"
    description_path = data_dir / "description.txt"

    try:
        raw: Any = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"No se pudo leer {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("config.json debe contener un objeto JSON")

    categories: dict[str, dict[str, str]] = {}
    for name, values in raw.items():
        if not isinstance(name, str) or not isinstance(values, dict):
            raise ConfigError(f"Categoría inválida en config.json: {name!r}")
        cleaned: dict[str, str] = {}
        for key, value in values.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ConfigError(f"Valor inválido en la categoría {name!r}: {key!r}")
            cleaned[key] = value
        categories[name] = cleaned

    try:
        description = description_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"No se pudo leer {description_path}: {exc}") from exc

    return Config(categories=categories, description=description)


def title_for(config: Config, category: str, brand: str | None) -> str:
    """Devuelve el título de la variante de marca, o ``default``."""
    values = config.categories.get(category)
    if values is None:
        raise ConfigError(f"Categoría no configurada: {category!r}")
    key = brand.lower() if brand else "default"
    return values.get(key, values.get("default", ""))


def load_reply_template(data_dir: Path) -> str:
    """Lee la plantilla global de respuesta; falla si falta o está vacía."""
    path = data_dir / "reply_added_favorites.txt"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"No se pudo leer {path}: {exc}") from exc
    if not text.strip():
        raise ConfigError(f"La plantilla {path} está vacía")
    return text.strip()
