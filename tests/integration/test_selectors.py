from __future__ import annotations

import re
from pathlib import Path

from vinted_anuncios.adapters import selectors

SNAPSHOT = Path(__file__).resolve().parents[1] / "fixtures" / "vinted_snapshot.html"
SELECTOR_RE = re.compile(r"^\[([^=]+)='([^']+)'\]$")


def test_todos_los_selectores_aparecen_en_el_snapshot() -> None:
    html = SNAPSHOT.read_text(encoding="utf-8")
    checked = 0
    for name in dir(selectors):
        value = getattr(selectors, name)
        if not isinstance(value, str) or not value.startswith("[data-vinted"):
            continue
        match = SELECTOR_RE.match(value)
        assert match is not None, f"Selector no válido: {name}"
        attribute, token = match.groups()
        assert f'{attribute}="{token}"' in html, f"{name} no aparece en el snapshot"
        checked += 1
    assert checked >= 10


def test_texto_disparador_esta_en_el_snapshot() -> None:
    html = SNAPSHOT.read_text(encoding="utf-8")
    assert selectors.FAVORITE_TEXT in html
