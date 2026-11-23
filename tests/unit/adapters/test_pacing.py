from __future__ import annotations

from vinted_anuncios.shared.pause import ActionPacer


def test_el_pacer_duerme_el_valor_generado() -> None:
    sleeps: list[float] = []
    pacer = ActionPacer(0.5, 1.5, uniform=lambda _min, _max: 0.8, sleep=sleeps.append)

    pacer.pause()

    assert sleeps == [0.8]


def test_el_pacer_no_duerme_si_el_rango_es_cero() -> None:
    sleeps: list[float] = []
    pacer = ActionPacer(0.0, 0.0, uniform=lambda _min, _max: 0.0, sleep=sleeps.append)

    pacer.pause()

    assert sleeps == []
