from __future__ import annotations

import shutil
from pathlib import Path


class FilesystemListingStore:
    """Borra solo carpetas hoja de anuncio: ``Data/<Cuenta>/<Categoría>/<Anuncio>``."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir.resolve()

    def delete(self, folder: Path) -> bool:
        path = folder.resolve()
        try:
            relative = path.relative_to(self._data_dir)
        except ValueError as exc:
            raise ValueError(f"La carpeta {folder} no está dentro de {self._data_dir}") from exc
        if len(relative.parts) != 3:
            raise ValueError(f"La carpeta {folder} no es un anuncio; no se borra")
        if not path.is_dir():
            return False
        shutil.rmtree(path)
        return True
