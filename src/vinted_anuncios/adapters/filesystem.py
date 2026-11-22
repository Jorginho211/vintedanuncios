from __future__ import annotations

import shutil
from pathlib import Path


class FilesystemListingStore:
    """Elimina la carpeta de un anuncio ya publicado."""

    def delete(self, folder: Path) -> bool:
        shutil.rmtree(folder)
        return True
