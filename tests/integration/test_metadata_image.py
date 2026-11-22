from __future__ import annotations

from pathlib import Path

import pytest

from vinted_anuncios.metadata import parse_caption_from_filename

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_lectura_de_caption_desde_nombre_de_archivo_real() -> None:
    photos = [item for item in FIXTURES.iterdir() if item.is_file() and ";" in item.stem]
    if not photos:
        pytest.skip("Falta una foto con la caption en el nombre del archivo")
    caption = parse_caption_from_filename(photos[0])
    assert caption.price == 24.95
    assert (caption.width_cm, caption.length_cm) == (50.0, 60.0)
    assert caption.brand == "Nike"
    assert caption.model == "35A"
