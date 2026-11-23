from __future__ import annotations

import pytest
from selenium.common.exceptions import StaleElementReferenceException

from vinted_anuncios.adapters.vinted_wait import retry_on_stale


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
