from __future__ import annotations

from pathlib import Path

import pytest

from vinted_anuncios.shared.metadata import (
    CaptionError,
    caption_from_filename,
    parse_caption,
    parse_caption_from_filename,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("24.95;50x60;Nike;35A", (24.95, 50.0, 60.0, "Nike", "35A")),
        ("25;40x30", (25.0, 40.0, 30.0, None, None)),
        ("25;40x30;Levis", (25.0, 40.0, 30.0, "Levis", None)),
        ("25;40x30;Levis;Air Max 90", (25.0, 40.0, 30.0, "Levis", "Air Max 90")),
        ("25;40x30;Levis;", (25.0, 40.0, 30.0, "Levis", None)),
        ("25;40x30;;", (25.0, 40.0, 30.0, None, None)),
        ("25,50;40x30", (25.5, 40.0, 30.0, None, None)),
        (" 25 ; 40 X 30 ; Nike ", (25.0, 40.0, 30.0, "Nike", None)),
    ],
)
def test_parse_caption(
    raw: str, expected: tuple[float, float, float, str | None, str | None]
) -> None:
    caption = parse_caption(raw)
    assert (
        caption.price,
        caption.width_cm,
        caption.length_cm,
        caption.brand,
        caption.model,
    ) == expected


@pytest.mark.parametrize("raw", ["25", "abc;40x30", "25;anchoxlargo", "25;40x30;a;b;c"])
def test_parse_caption_rechaza_formatos_invalidos(raw: str) -> None:
    with pytest.raises(CaptionError):
        parse_caption(raw)


def test_caption_from_filename_quita_la_extension() -> None:
    path = Path("24.95;50x60;Nike;35A.HEIC")
    assert caption_from_filename(path) == "24.95;50x60;Nike;35A"


def test_parse_caption_from_filename() -> None:
    path = Path("24.95;50x60;Nike;35A.HEIC")
    caption = parse_caption_from_filename(path)
    assert caption.price == 24.95
    assert (caption.width_cm, caption.length_cm) == (50.0, 60.0)
    assert caption.brand == "Nike"
    assert caption.model == "35A"
