from __future__ import annotations

from ...shared.config import Config, ConfigError, title_for
from ...shared.metadata import CaptionError
from ...shared.models import Caption, Listing, ScanResult
from .query import (
    IMAGE_SUFFIXES,
    UNSUPPORTED_IMAGE_SUFFIXES,
    ScanError,
    ScanListings,
    caption_from_images,
    form_category_from,
    subdirectories,
)


def _full_title(config: Config, category: str, caption: Caption) -> str:
    """Construye `<Marca> <Modelo> <Titulo>` con la variante de config.json."""
    base = title_for(config, category, caption.brand)
    return " ".join(part for part in (caption.brand, caption.model, base) if part).strip()


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
                        unsupported = sorted(
                            item.name
                            for item in folder.iterdir()
                            if item.is_file() and item.suffix.lower() in UNSUPPORTED_IMAGE_SUFFIXES
                        )
                        if unsupported:
                            raise ScanError(
                                "Vinted no acepta imágenes HEIC/HEIF; conviértelas a JPEG: "
                                + ", ".join(unsupported)
                            )
                        raise ScanError("la carpeta no contiene imágenes")

                    caption = caption_from_images(images)
                    config_category = category_dir.name
                    listings.append(
                        Listing(
                            account=account_dir.name,
                            config_category=config_category,
                            form_category=form_category_from(config_category),
                            folder=folder,
                            images=images,
                            caption=caption,
                            title=_full_title(query.config, config_category, caption),
                            description=query.config.description,
                        )
                    )
                except (ConfigError, CaptionError, ScanError, OSError) as exc:
                    errors.append(f"{folder}: {exc}")

    return ScanResult(listings=tuple(listings), errors=tuple(errors))
