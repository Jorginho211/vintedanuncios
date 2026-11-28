from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from vinted_anuncios import scheduler as scheduler_module
from vinted_anuncios.shared.models import Mode
from vinted_anuncios.shared.settings import load_settings

LOGGER = logging.getLogger("test-scheduler")
TZ = ZoneInfo("Europe/Madrid")


@dataclass
class Job:
    func: Callable[..., None]
    trigger: object
    kwargs: dict[str, object]
    id: str
    max_instances: int
    coalesce: bool


class FakeScheduler:
    def __init__(self, timezone: object) -> None:
        self.timezone = timezone
        self.jobs: dict[str, Job] = {}
        self.started = False

    def add_job(
        self,
        func: Callable[..., None],
        trigger: object = None,
        *,
        kwargs: dict[str, object] | None = None,
        id: str,
        max_instances: int,
        coalesce: bool,
    ) -> None:
        self.jobs[id] = Job(func, trigger, kwargs or {}, id, max_instances, coalesce)

    def get_job(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)

    def reschedule_job(self, job_id: str, *, trigger: object) -> None:
        self.jobs[job_id].trigger = trigger

    def start(self) -> None:
        self.started = True


def test_start_registra_publicacion_y_reply_con_intervalo_aleatorio(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeScheduler(timezone=TZ)
    monkeypatch.setattr(scheduler_module, "BlockingScheduler", lambda timezone: fake)

    publish_calls: list[dict[str, object]] = []
    reply_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        scheduler_module, "run_publish", lambda **kwargs: publish_calls.append(kwargs)
    )
    monkeypatch.setattr(
        scheduler_module,
        "run_reply",
        lambda *args, **kwargs: reply_calls.append(kwargs or {"args": args}),
    )

    settings = load_settings({"DATA_DIR": str(tmp_path)})
    current = datetime(2026, 1, 1, 8, 0, tzinfo=TZ)
    scheduler_module.start(
        settings,
        Mode.DRY_RUN,
        logger=LOGGER,
        randint=lambda _a, _b: 45,
        now=lambda: current,
    )

    assert fake.started is True
    assert sorted(fake.jobs) == ["publicacion_diaria", "respuesta_favoritos"]

    publish = fake.jobs["publicacion_diaria"]
    assert publish.max_instances == 1 and publish.coalesce is True
    assert "hour='16'" in str(publish.trigger)

    reply = fake.jobs["respuesta_favoritos"]
    assert reply.max_instances == 1 and reply.coalesce is True
    assert "2026-01-01 08:45:00" in str(reply.trigger)

    publish.func(**publish.kwargs)
    assert publish_calls == [{"settings": settings, "mode": Mode.DRY_RUN, "logger": LOGGER}]

    current = datetime(2026, 1, 1, 8, 45, tzinfo=TZ)
    reply.func(**reply.kwargs)
    assert len(reply_calls) == 1
    assert reply_calls[0]["logger"] is LOGGER
    assert "2026-01-01 09:30:00" in str(fake.jobs["respuesta_favoritos"].trigger)


@pytest.mark.parametrize(
    ("now", "delay", "jitter", "expected"),
    [
        (
            datetime(2026, 1, 1, 0, 30, tzinfo=TZ),
            45,
            15,
            datetime(2026, 1, 1, 8, 15, tzinfo=TZ),
        ),  # 01:15 cae en la franja: se difiere con jitter
        (
            datetime(2026, 1, 1, 0, 30, tzinfo=TZ),
            30,
            0,
            datetime(2026, 1, 1, 8, 0, tzinfo=TZ),
        ),  # 01:00 queda bloqueado; 08:00 es el primer disparo permitido
        (
            datetime(2026, 1, 1, 7, 30, tzinfo=TZ),
            45,
            0,
            datetime(2026, 1, 1, 8, 15, tzinfo=TZ),
        ),  # 08:15 ya está fuera de la franja
        (
            datetime(2026, 1, 1, 8, 0, tzinfo=TZ),
            30,
            0,
            datetime(2026, 1, 1, 8, 30, tzinfo=TZ),
        ),  # límite inferior permitido
        (
            datetime(2026, 1, 1, 23, 30, tzinfo=TZ),
            60,
            0,
            datetime(2026, 1, 2, 0, 30, tzinfo=TZ),
        ),  # cruza medianoche sin entrar en la franja
        (
            datetime(2026, 1, 1, 2, 0, tzinfo=TZ),
            30,
            30,
            datetime(2026, 1, 1, 8, 30, tzinfo=TZ),
        ),  # arranque dentro de la franja
    ],
)
def test_next_reply_run_respeta_la_franja_nocturna(
    now: datetime, delay: int, jitter: int, expected: datetime
) -> None:
    valores = iter([delay, jitter])

    def randint(_a: int, _b: int) -> int:
        return next(valores)

    assert scheduler_module._next_reply_run(now=now, randint=randint) == expected


def test_next_reply_run_usa_la_zona_horaria_del_reloj() -> None:
    timezone = ZoneInfo("America/New_York")
    now = datetime(2026, 6, 1, 2, 0, tzinfo=timezone)
    valores = iter([30, 10])

    def randint(_a: int, _b: int) -> int:
        return next(valores)

    assert scheduler_module._next_reply_run(now=now, randint=randint) == datetime(
        2026, 6, 1, 8, 10, tzinfo=timezone
    )


def test_start_difiere_el_primer_reply_de_madrugada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeScheduler(timezone=TZ)
    monkeypatch.setattr(scheduler_module, "BlockingScheduler", lambda timezone: fake)
    monkeypatch.setattr(scheduler_module, "run_publish", lambda **kwargs: None)
    monkeypatch.setattr(scheduler_module, "run_reply", lambda *args, **kwargs: None)

    calls: list[tuple[int, int]] = []
    valores = iter([45, 15])

    def randint(minimum: int, maximum: int) -> int:
        calls.append((minimum, maximum))
        return next(valores)

    settings = load_settings({"DATA_DIR": str(tmp_path)})
    current = datetime(2026, 1, 1, 0, 30, tzinfo=TZ)
    scheduler_module.start(
        settings,
        Mode.DRY_RUN,
        logger=LOGGER,
        randint=randint,
        now=lambda: current,
    )

    assert calls == [(30, 60), (0, 30)]
    assert "2026-01-01 08:15:00" in str(fake.jobs["respuesta_favoritos"].trigger)
