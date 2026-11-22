from __future__ import annotations

from pathlib import Path

from .config import Config, ConfigError, title_for
from .metadata import CaptionError, parse_caption_from_filename
from .models import Caption, Listing, ScanResult

IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".heic", ".heif"})


class ScanError(ValueError):
    """Una carpeta no se pudo convertir en anuncio."""


def _subdirectories(path: Path) -> list[Path]:
    return sorted(
        item for item in path.iterdir() if item.is_dir() and not item.name.startswith(".")
    )


def _caption_from_images(images: tuple[Path, ...]) -> Caption:
    last_error = "ninguna imagen en la carpeta"
    for image in images:
        try:
            return parse_caption_from_filename(image)
        except CaptionError as exc:
            last_error = str(exc)
    raise ScanError(f"ningún archivo tiene una caption válida en el nombre: {last_error}")


def scan(data_dir: Path, config: Config) -> ScanResult:
    """Recorre ``Data`` y devuelve anuncios + errores, sin usar Selenium."""
    if not data_dir.is_dir():
        raise FileNotFoundError(f"No existe el directorio {data_dir}")

    listings: list[Listing] = []
    errors: list[str] = []

    for account_dir in _subdirectories(data_dir):
        for category_dir in _subdirectories(account_dir):
            for folder in _subdirectories(category_dir):
                try:
                    images = tuple(
                        sorted(
                            item
                            for item in folder.iterdir()
                            if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES
                        )
                    )
                    if not images:
                        raise ScanError("la carpeta no contiene imágenes")

                    caption = _caption_from_images(images)
                    title = title_for(config, category_dir.name, caption.brand)
                    listings.append(
                        Listing(
                            account=account_dir.name,
                            category=category_dir.name,
                            folder=folder,
                            images=images,
                            caption=caption,
                            title=title,
                            description=config.description,
                        )
                    )
                except (ConfigError, CaptionError, ScanError, OSError) as exc:
                    errors.append(f"{folder}: {exc}")

    return ScanResult(listings=tuple(listings), errors=tuple(errors))
