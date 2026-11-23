from __future__ import annotations

from pathlib import Path

import pytest

from vinted_anuncios.adapters.filesystem import FilesystemListingStore


def _tree(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    data_dir = tmp_path / "Data"
    category = data_dir / "CuentaA" / "Pantalones Anchos"
    folder = category / "Anuncio 1"
    folder.mkdir(parents=True)
    (folder / "foto.JPG").write_bytes(b"foto")
    return data_dir, folder, category, data_dir / "CuentaA"


def test_borra_solo_la_carpeta_hoja_del_anuncio(tmp_path: Path) -> None:
    data_dir, folder, category, account = _tree(tmp_path)
    store = FilesystemListingStore(data_dir)

    assert store.delete(folder) is True
    assert not folder.exists()
    assert category.is_dir()
    assert account.is_dir()
    assert data_dir.is_dir()


def test_rechaza_borrar_la_carpeta_de_categoria(tmp_path: Path) -> None:
    data_dir, _folder, category, _account = _tree(tmp_path)
    with pytest.raises(ValueError, match="no es un anuncio"):
        FilesystemListingStore(data_dir).delete(category)
    assert category.is_dir()


def test_rechaza_borrar_la_carpeta_de_cuenta(tmp_path: Path) -> None:
    data_dir, _folder, _category, account = _tree(tmp_path)
    with pytest.raises(ValueError, match="no es un anuncio"):
        FilesystemListingStore(data_dir).delete(account)
    assert account.is_dir()


def test_rechaza_borrar_fuera_del_arbol(tmp_path: Path) -> None:
    data_dir, _folder, _category, _account = _tree(tmp_path)
    other = tmp_path / "Otro" / "Cuenta" / "Categoria" / "Anuncio"
    other.mkdir(parents=True)
    with pytest.raises(ValueError, match="no está dentro"):
        FilesystemListingStore(data_dir).delete(other)
    assert other.is_dir()
