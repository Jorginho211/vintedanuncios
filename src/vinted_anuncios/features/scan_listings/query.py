from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...shared.config import Config
from ...shared.metadata import CaptionError, parse_caption_from_filename
from ...shared.models import Caption

IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".heic", ".heif"})


class ScanError(ValueError):
    """Una carpeta no se pudo convertir en anuncio."""


@dataclass(frozen=True, slots=True)
class ScanListings:
    """Consulta: resolver los anuncios pendientes desde el árbol de ``Data``."""

    data_dir: Path
    config: Config


def subdirectories(path: Path) -> list[Path]:
    return sorted(
        item for item in path.iterdir() if item.is_dir() and not item.name.startswith(".")
    )


def caption_from_images(images: tuple[Path, ...]) -> Caption:
    last_error = "ninguna imagen en la carpeta"
    for image in images:
        try:
            return parse_caption_from_filename(image)
        except CaptionError as exc:
            last_error = str(exc)
    raise ScanError(f"ningún archivo tiene una caption válida en el nombre: {last_error}")


__all__ = [
    "IMAGE_SUFFIXES",
    "ScanError",
    "ScanListings",
    "caption_from_images",
    "subdirectories",
]
