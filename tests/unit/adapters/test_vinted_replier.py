from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field

import pytest
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.keys import Keys

from vinted_anuncios.adapters import selectors
from vinted_anuncios.adapters import vinted_replier as replier_module
from vinted_anuncios.adapters.vinted_replier import VintedFavoriteReplier
from vinted_anuncios.shared.ports import DriverPort, ElementPort
from vinted_anuncios.shared.settings import Settings, load_settings

LOGGER = logging.getLogger("test")
TEMPLATE = "Gracias por tu interés"


@dataclass
class Calls:
    fills: list[tuple[str, str]] = field(default_factory=list)
    clicks: list[str] = field(default_factory=list)
    sends: list[tuple[str, str]] = field(default_factory=list)
    opened: list[str] = field(default_factory=list)
    closed: list[str] = field(default_factory=list)


class FakeElement:
    def __init__(self, text: str = "", attributes: dict[str, str] | None = None) -> None:
        self.text = text
        self._attributes = attributes or {}

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value

    def clear(self) -> None:
        pass

    def send_keys(self, *value: str) -> None:
        pass

    def click(self) -> None:
        pass

    def get_attribute(self, name: str) -> str | None:
        return self._attributes.get(name)

    def find_element(self, by: str, value: str) -> ElementPort:
        return FakeElement()


class FakeDriver:
    def __init__(self, wrappers: Sequence[ElementPort]) -> None:
        self._wrappers = wrappers
        self.urls: list[str] = []
        self.current_window_handle = "main"
        self.window_handles = ("main",)

    def get(self, url: str) -> None:
        self.urls.append(url)

    def find_element(self, by: str, value: str) -> ElementPort:
        return FakeElement()

    def find_elements(self, by: str, value: str) -> Sequence[ElementPort]:
        return self._wrappers

    @property
    def current_url(self) -> str:
        return "https://www.vinted.es/member/notifications"

    def execute_script(self, script: str, *args: object) -> object:
        return False

    def switch_to_window(self, handle: str) -> None:
        self.current_window_handle = handle

    def close(self) -> None:
        pass

    def quit(self) -> None:
        pass


def _settings() -> Settings:
    return load_settings(
        {
            "DATA_DIR": "Data",
            "SELENIUM_ACTION_DELAY_MIN": "0",
            "SELENIUM_ACTION_DELAY_MAX": "0",
        }
    )


def _wrapper(notification_id: str) -> FakeElement:
    return FakeElement(
        text="Ha añadido el artículo a sus favoritos",
        attributes={
            "data-notification-id": notification_id,
            "href": f"https://www.vinted.es/messages/{notification_id}",
        },
    )


def _build(
    monkeypatch: pytest.MonkeyPatch,
    wrappers: Sequence[ElementPort],
    *,
    send: bool,
    placeholders: Sequence[str] | None = None,
    replied: bool = False,
    has_messages: bool = False,
    fail_first_message: bool = False,
) -> tuple[VintedFavoriteReplier, FakeDriver, Calls]:
    driver = FakeDriver(wrappers)
    calls = Calls()
    prices = list(placeholders or ["24,95 €"])
    message_attempts = 0

    class NoPacer:
        def pause(self) -> None:
            pass

    monkeypatch.setattr(replier_module, "ActionPacer", lambda *_args: NoPacer())
    monkeypatch.setattr(replier_module, "wait_for_page_ready", lambda *_args: None)

    def fake_wait_for_all(*_args: object) -> Sequence[ElementPort]:
        return wrappers

    def fake_scroll(*_args: object, **_kwargs: object) -> bool:
        return False

    def fake_open_tab(_driver: DriverPort, url: str) -> str:
        calls.opened.append(url)
        return "tab"

    def fake_close(_driver: DriverPort, main_handle: str) -> None:
        calls.closed.append(main_handle)

    def fake_wait_for(_driver: DriverPort, css: str, _timeout: float) -> ElementPort:
        if css == selectors.SELECTOR_CONVERSATION_MESSAGES:
            if has_messages:
                return FakeElement()
            raise TimeoutException("sin mensajes en la conversación")
        if css == selectors.SELECTOR_REPLIED_MARKER:
            if replied:
                return FakeElement()
            raise TimeoutException("sin marcador de respondida")
        if css == selectors.SELECTOR_OFFER_PRICE_INPUT:
            # La modal se espera antes de comprobar si está respondida y después
            # al leer el precio: mismo placeholder para la misma conversación.
            index = max(len(calls.opened) - 1, 0)
            return FakeElement(attributes={"placeholder": prices[index]})
        raise AssertionError(f"Selector inesperado: {css}")

    def fake_fill(_driver: DriverPort, css: str, value: str, _timeout: float) -> None:
        calls.fills.append((css, value))

    def fake_click(_driver: DriverPort, css: str, _timeout: float) -> None:
        calls.clicks.append(css)

    def fake_send_keys(_driver: DriverPort, css: str, value: str, _timeout: float) -> None:
        nonlocal message_attempts
        calls.sends.append((css, value))
        if value == TEMPLATE:
            message_attempts += 1
            if fail_first_message and message_attempts == 1:
                raise WebDriverException("fallo al enviar el mensaje")

    monkeypatch.setattr(replier_module, "wait_for_all", fake_wait_for_all)
    monkeypatch.setattr(replier_module, "scroll_window", fake_scroll)
    monkeypatch.setattr(replier_module, "open_tab", fake_open_tab)
    monkeypatch.setattr(replier_module, "close_current_tab", fake_close)
    monkeypatch.setattr(replier_module, "wait_for", fake_wait_for)
    monkeypatch.setattr(replier_module, "fill", fake_fill)
    monkeypatch.setattr(replier_module, "click_css", fake_click)
    monkeypatch.setattr(replier_module, "send_keys_css", fake_send_keys)

    replier = VintedFavoriteReplier(driver, _settings(), LOGGER, account="Cuenta", send=send)
    return replier, driver, calls


def test_responde_favorito_pendiente_con_la_oferta_y_el_mensaje(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrapper = _wrapper("n1")
    replier, driver, calls = _build(monkeypatch, [wrapper], send=True)

    result = replier.scan_favorites(TEMPLATE)

    notice = result.notifications[0]
    assert driver.urls == [selectors.MEMBER_NOTIFICATIONS_URL]
    assert notice.replied is False
    assert notice.previous_price == "24,95"
    assert notice.offered_price == "22,95"
    assert notice.message_sent is True
    assert calls.fills == [(selectors.SELECTOR_OFFER_PRICE_INPUT, "22,95")]
    assert calls.clicks == [selectors.SELECTOR_OFFER_SUBMIT]
    assert calls.sends == [
        (selectors.SELECTOR_COMPOSER_INPUT, TEMPLATE),
        (selectors.SELECTOR_COMPOSER_INPUT, Keys.ENTER),
    ]
    assert calls.opened == ["https://www.vinted.es/messages/n1"]
    assert calls.closed == ["main"]
    assert result.errors == ()


def test_modos_real_sin_publicar_no_escriben(monkeypatch: pytest.MonkeyPatch) -> None:
    replier, _driver, calls = _build(monkeypatch, [_wrapper("n1")], send=False)

    result = replier.scan_favorites(TEMPLATE)

    assert result.notifications[0].offered_price == "22,95"
    assert result.notifications[0].message_sent is False
    assert calls.fills == []
    assert calls.clicks == []
    assert calls.sends == []


def test_primera_respondida_detiene_el_barrido(monkeypatch: pytest.MonkeyPatch) -> None:
    replier, _driver, calls = _build(
        monkeypatch,
        [_wrapper("n1"), _wrapper("n2")],
        send=True,
        replied=True,
    )

    result = replier.scan_favorites(TEMPLATE)

    assert len(result.notifications) == 1
    assert result.notifications[0].replied is True
    assert result.stopped_reason == "replied_found"
    assert calls.opened == ["https://www.vinted.es/messages/n1"]
    assert calls.clicks == []
    assert calls.sends == []


def test_conversacion_con_mensajes_se_considera_respondida(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replier, _driver, calls = _build(
        monkeypatch,
        [_wrapper("n1")],
        send=True,
        has_messages=True,
    )

    result = replier.scan_favorites(TEMPLATE)

    assert len(result.notifications) == 1
    assert result.notifications[0].replied is True
    assert result.stopped_reason == "replied_found"
    assert calls.clicks == []
    assert calls.sends == []


def test_precio_invalido_se_omite_y_continua(monkeypatch: pytest.MonkeyPatch) -> None:
    replier, _driver, calls = _build(
        monkeypatch,
        [_wrapper("n1"), _wrapper("n2")],
        send=True,
        placeholders=["abc", "24,95 €"],
    )

    result = replier.scan_favorites(TEMPLATE)

    assert len(result.notifications) == 2
    assert result.notifications[0].offered_price is None
    assert result.notifications[0].message_sent is False
    assert result.notifications[1].message_sent is True
    assert len(result.errors) == 1
    assert "notificación n1" in result.errors[0]
    assert calls.fills == [(selectors.SELECTOR_OFFER_PRICE_INPUT, "22,95")]


def test_fallo_del_mensaje_no_detiene_la_siguiente(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replier, _driver, calls = _build(
        monkeypatch,
        [_wrapper("n1"), _wrapper("n2")],
        send=True,
        placeholders=["24,95 €", "24,95 €"],
        fail_first_message=True,
    )

    result = replier.scan_favorites(TEMPLATE)

    assert result.notifications[0].message_sent is False
    assert result.notifications[1].message_sent is True
    assert len(result.errors) == 1
    assert "fallo al responder" in result.errors[0]
    assert len(calls.clicks) == 2
