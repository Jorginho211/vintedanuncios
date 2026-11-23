from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from vinted_anuncios.adapters import vinted_publisher
from vinted_anuncios.adapters.vinted_publisher import VintedListingPublisher
from vinted_anuncios.shared.settings import load_settings


def _publisher(
    monkeypatch: pytest.MonkeyPatch, suggested: str
) -> tuple[VintedListingPublisher, list[dict[str, str]]]:
    element = MagicMock()
    element.get_attribute.return_value = suggested
    monkeypatch.setattr(vinted_publisher, "wait_for", lambda *_args, **_kwargs: element)
    publisher = VintedListingPublisher(
        MagicMock(), load_settings({}), logging.getLogger("test"), submit=False
    )
    calls: list[dict[str, str]] = []
    monkeypatch.setattr(publisher, "_choose_from_search", lambda **kw: calls.append(kw))
    return publisher, calls


def test_conserva_la_marca_que_vinted_ya_sugirio(monkeypatch: pytest.MonkeyPatch) -> None:
    publisher, calls = _publisher(monkeypatch, "Levi's")

    publisher._ensure_brand("Levis")

    assert calls == []


def test_cambia_la_marca_si_la_sugerencia_no_coincide(monkeypatch: pytest.MonkeyPatch) -> None:
    publisher, calls = _publisher(monkeypatch, "Otra marca")

    publisher._ensure_brand("Levis")

    assert len(calls) == 1
    assert calls[0]["value"] == "Levis"


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
