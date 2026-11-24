from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from selenium.common.exceptions import StaleElementReferenceException

from vinted_anuncios.adapters.vinted_wait import retry_on_stale, scroll_next_page


def test_reintenta_si_el_nodo_esta_obsoleto() -> None:
    attempts: list[int] = []

    def action() -> str:
        attempts.append(1)
        if len(attempts) < 3:
            raise StaleElementReferenceException("obsoleto")
        return "ok"

    assert retry_on_stale(action) == "ok"
    assert len(attempts) == 3


def test_agota_los_intentos_y_propaga_el_error() -> None:
    def action() -> str:
        raise StaleElementReferenceException("obsoleto")

    with pytest.raises(StaleElementReferenceException):
        retry_on_stale(action, attempts=2)


def test_el_scroll_busca_el_ancestro_con_desplazamiento() -> None:
    driver = MagicMock()
    driver.execute_script.return_value = True

    assert scroll_next_page(driver, "[role='radio'][id^='brand-']") is True

    script, css = driver.execute_script.call_args.args
    assert "scrollHeight <= node.clientHeight" in script
    assert "node.scrollTop" in script
    assert css == "[role='radio'][id^='brand-']"


def test_el_scroll_informa_si_no_puede_avanzar() -> None:
    driver = MagicMock()
    driver.execute_script.return_value = False

    assert scroll_next_page(driver, "[role='radio']") is False
