from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from vinted_anuncios.adapters import vinted_publisher
from vinted_anuncios.adapters.vinted_publisher import DEFAULT_BRAND, VintedListingPublisher
from vinted_anuncios.shared.models import Caption, Listing
from vinted_anuncios.shared.settings import load_settings


def _publisher(
    monkeypatch: pytest.MonkeyPatch, suggested: str
) -> tuple[VintedListingPublisher, list[dict[str, str]], list[str]]:
    element = MagicMock()
    element.get_attribute.return_value = suggested
    monkeypatch.setattr(vinted_publisher, "wait_for", lambda *_args, **_kwargs: element)
    publisher = VintedListingPublisher(
        MagicMock(), load_settings({}), logging.getLogger("test"), submit=False
    )
    calls: list[dict[str, str]] = []
    scroll_calls: list[str] = []
    monkeypatch.setattr(publisher, "_choose_from_search", lambda **kw: calls.append(kw))
    monkeypatch.setattr(
        publisher, "_choose_default_brand_by_scroll", lambda: scroll_calls.append("scroll")
    )
    return publisher, calls, scroll_calls


def _listing(brand: str | None) -> Listing:
    return Listing(
        account="Cuenta A",
        config_category="Cortavientos.General",
        form_category="Cortavientos",
        folder=Path("Data/Cuenta A/Cortavientos.General/Anuncio 1"),
        images=(),
        caption=Caption(price=25.0, width_cm=40.0, length_cm=30.0, brand=brand, model=None),
        title="Título por defecto",
        description="Descripción",
        size="S",
    )


def test_conserva_la_marca_que_vinted_ya_sugirio(monkeypatch: pytest.MonkeyPatch) -> None:
    publisher, calls, scroll_calls = _publisher(monkeypatch, "Levi's")

    publisher._ensure_brand("Levis")

    assert calls == []
    assert scroll_calls == []


def test_cambia_la_marca_si_la_sugerencia_no_coincide(monkeypatch: pytest.MonkeyPatch) -> None:
    publisher, calls, scroll_calls = _publisher(monkeypatch, "Otra marca")

    publisher._ensure_brand("Levis")

    assert len(calls) == 1
    assert calls[0]["value"] == "Levis"
    assert scroll_calls == []


def test_sustituye_la_sugerencia_de_vinted_por_la_marca_por_defecto(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publisher, calls, scroll_calls = _publisher(monkeypatch, "Nike")

    publisher._ensure_brand(DEFAULT_BRAND)

    assert calls == []
    assert scroll_calls == ["scroll"]


def test_conserva_la_sugerencia_de_la_marca_por_defecto_en_minusculas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publisher, calls, scroll_calls = _publisher(monkeypatch, "vintage dressing")

    publisher._ensure_brand(DEFAULT_BRAND)

    assert calls == []
    assert scroll_calls == []


def test_selecciona_la_marca_por_defecto_tras_desplazar_el_listado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publisher = VintedListingPublisher(
        MagicMock(), load_settings({}), logging.getLogger("test"), submit=False
    )
    wrong = MagicMock()
    wrong.text = "Levi's"
    right = MagicMock()
    right.text = "Vintage dressing"
    pages = [[wrong], [wrong, right], [wrong, right]]
    monkeypatch.setattr(vinted_publisher, "wait_for_all", lambda *_a, **_k: pages.pop(0))
    monkeypatch.setattr(vinted_publisher, "click_css", lambda *_a, **_k: None)
    monkeypatch.setattr(vinted_publisher, "scroll_next_page", lambda *_a: True)
    clicked: list[object] = []
    monkeypatch.setattr(
        vinted_publisher, "click_js", lambda _driver, element: clicked.append(element)
    )
    monkeypatch.setattr(publisher, "_pace", lambda: None)

    publisher._choose_default_brand_by_scroll()

    assert clicked == [right]


def test_falla_si_la_marca_por_defecto_no_aparece_al_final_del_listado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publisher = VintedListingPublisher(
        MagicMock(), load_settings({}), logging.getLogger("test"), submit=False
    )
    option = MagicMock()
    option.text = "Levi's"
    scrolls = iter([True, False])
    monkeypatch.setattr(vinted_publisher, "wait_for_all", lambda *_a, **_k: [option])
    monkeypatch.setattr(vinted_publisher, "click_css", lambda *_a, **_k: None)
    monkeypatch.setattr(vinted_publisher, "scroll_next_page", lambda *_a: next(scrolls))
    monkeypatch.setattr(publisher, "_pace", lambda: None)

    with pytest.raises(RuntimeError, match="tras recorrer el listado"):
        publisher._choose_default_brand_by_scroll()


def test_falla_si_el_listado_de_marcas_no_se_desplaza(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publisher = VintedListingPublisher(
        MagicMock(), load_settings({}), logging.getLogger("test"), submit=False
    )
    option = MagicMock()
    option.text = "Levi's"
    monkeypatch.setattr(vinted_publisher, "wait_for_all", lambda *_a, **_k: [option])
    monkeypatch.setattr(vinted_publisher, "click_css", lambda *_a, **_k: None)
    monkeypatch.setattr(vinted_publisher, "scroll_next_page", lambda *_a: False)
    monkeypatch.setattr(publisher, "_pace", lambda: None)

    with pytest.raises(RuntimeError, match="tras recorrer el listado"):
        publisher._choose_default_brand_by_scroll()


@pytest.mark.parametrize(
    ("brand", "expected"),
    [(None, "Vintage Dressing"), ("Levis", "Levis")],
)
def test_el_campo_marca_usa_el_fallback_solo_si_falta_la_marca(
    monkeypatch: pytest.MonkeyPatch, brand: str | None, expected: str
) -> None:
    publisher = VintedListingPublisher(
        MagicMock(), load_settings({}), logging.getLogger("test"), submit=False
    )
    for name in (
        "_open_form",
        "_upload_photos",
        "_fill_text",
        "_choose_category",
        "_choose_size",
        "_choose_color",
        "_choose_condition",
        "_choose_shipping",
        "_leave_form",
    ):
        monkeypatch.setattr(publisher, name, lambda *_args, **_kwargs: None)
    brands: list[str] = []
    monkeypatch.setattr(publisher, "_ensure_brand", brands.append)

    result = publisher.publish(_listing(brand))

    assert result.ok
    assert brands == [expected]


def test_elige_la_primera_opcion_de_talla_presente_en_el_dom(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publisher = VintedListingPublisher(
        MagicMock(), load_settings({}), logging.getLogger("test"), submit=False
    )
    wrong = MagicMock()
    wrong.text = "W30"
    right = MagicMock()
    right.text = "ES 42"
    monkeypatch.setattr(vinted_publisher, "wait_for_all", lambda *_a, **_k: [wrong, right])
    monkeypatch.setattr(vinted_publisher, "click_css", lambda *_a, **_k: None)
    monkeypatch.setattr(publisher, "_pace", lambda: None)
    clicked: list[object] = []
    monkeypatch.setattr(
        vinted_publisher, "click_js", lambda _driver, element: clicked.append(element)
    )

    publisher._choose_size("W32 | ES42")

    assert clicked == [right]


def test_falla_si_vinted_no_ofrece_la_talla(monkeypatch: pytest.MonkeyPatch) -> None:
    publisher = VintedListingPublisher(
        MagicMock(), load_settings({}), logging.getLogger("test"), submit=False
    )
    option = MagicMock()
    option.text = "W30"
    monkeypatch.setattr(vinted_publisher, "wait_for_all", lambda *_a, **_k: [option])
    monkeypatch.setattr(vinted_publisher, "click_css", lambda *_a, **_k: None)
    monkeypatch.setattr(publisher, "_pace", lambda: None)

    with pytest.raises(RuntimeError, match="no ofreció la talla"):
        publisher._choose_size("W32 | ES42")


def test_configura_el_pacer_con_los_valores_de_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, float] = {}

    class FakePacer:
        def __init__(self, minimum: float, maximum: float) -> None:
            captured["min"] = minimum
            captured["max"] = maximum

        def pause(self) -> None:
            pass

    monkeypatch.setattr(vinted_publisher, "ActionPacer", FakePacer)
    settings = load_settings(
        {"SELENIUM_ACTION_DELAY_MIN": "0.2", "SELENIUM_ACTION_DELAY_MAX": "0.9"}
    )

    VintedListingPublisher(MagicMock(), settings, logging.getLogger("test"))

    assert captured == {"min": 0.2, "max": 0.9}
