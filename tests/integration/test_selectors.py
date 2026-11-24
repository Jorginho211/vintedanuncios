from __future__ import annotations

import re
from pathlib import Path

from vinted_anuncios.adapters import selectors

SNAPSHOT = Path(__file__).resolve().parents[1] / "fixtures" / "vinted_snapshot.html"
SELECTOR_RE = re.compile(r"^\[([^=]+)='([^']+)'\]$")

# Selectores de publicación validados contra el DOM real de CuentaA (plan 016).
REAL_SELECTORS = (
    "SELECTOR_SELL_LINK",
    "SELECTOR_COOKIES",
    "SELECTOR_PHOTO_INPUT",
    "SELECTOR_UPLOAD_LOADER",
    "SELECTOR_UPLOAD_ERROR",
    "SELECTOR_TITLE",
    "SELECTOR_DESCRIPTION",
    "SELECTOR_PRICE",
    "SELECTOR_CATEGORY",
    "SELECTOR_CATEGORY_SEARCH",
    "SELECTOR_CATEGORY_OPTION",
    "SELECTOR_BRAND",
    "SELECTOR_BRAND_SEARCH",
    "SELECTOR_BRAND_OPTION",
    "SELECTOR_SIZE",
    "SELECTOR_SIZE_CONTENT",
    "SELECTOR_SIZE_OPTION",
    "SELECTOR_SIZE_OPTION_ANY",
    "SELECTOR_COLOR",
    "SELECTOR_CONDITION",
    "SELECTOR_CONDITION_GOOD",
    "SELECTOR_PACKAGE_SMALL",
    "SELECTOR_SUBMIT",
    "SELECTOR_UNSAVED_DIALOG",
    "XPATH_COLOR_SUGGESTION",
    "XPATH_COLOR_FIRST",
    "XPATH_DISCARD_CHANGES",
)


def _fragments(selector: str) -> set[str]:
    """Extrae tokens identificables de un selector CSS o XPath."""
    tokens = set(re.findall(r"#([\w-]+)", selector))
    tokens |= set(re.findall(r"\.([\w-]+)", selector))
    tokens |= set(re.findall(r"['\"]([^'\"]+)['\"]", selector))
    return {token for token in tokens if len(token) > 1}


def test_los_selectores_reales_aparecen_en_el_snapshot() -> None:
    html = SNAPSHOT.read_text(encoding="utf-8")
    for name in REAL_SELECTORS:
        selector = getattr(selectors, name)
        assert any(
            token in html for token in _fragments(selector)
        ), f"{name} no aparece en el snapshot: {selector}"


def test_selectores_de_favoritos_aparecen_en_el_snapshot() -> None:
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
    assert checked >= 5


def test_texto_disparador_esta_en_el_snapshot() -> None:
    html = SNAPSHOT.read_text(encoding="utf-8")
    assert selectors.FAVORITE_TEXT in html
