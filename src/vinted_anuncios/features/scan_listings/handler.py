from __future__ import annotations

from ...shared.config import ConfigError, title_for
from ...shared.metadata import CaptionError
from ...shared.models import Listing, ScanResult
from .query import (
    IMAGE_SUFFIXES,
    ScanError,
    ScanListings,
    caption_from_images,
    subdirectories,
)


def handle(query: ScanListings) -> ScanResult:
    """Recorre ``Data`` y devuelve anuncios + errores, sin usar Selenium."""
    if not query.data_dir.is_dir():
        raise FileNotFoundError(f"No existe el directorio {query.data_dir}")

    listings: list[Listing] = []
    errors: list[str] = []

    for account_dir in subdirectories(query.data_dir):
        for category_dir in subdirectories(account_dir):
            for folder in subdirectories(category_dir):
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

                    caption = caption_from_images(images)
                    title = title_for(query.config, category_dir.name, caption.brand)
                    listings.append(
                        Listing(
                            account=account_dir.name,
                            category=category_dir.name,
                            folder=folder,
                            images=images,
                            caption=caption,
                            title=title,
                            description=query.config.description,
                        )
                    )
                except (ConfigError, CaptionError, ScanError, OSError) as exc:
                    errors.append(f"{folder}: {exc}")

    return ScanResult(listings=tuple(listings), errors=tuple(errors))
