from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from vinted_anuncios import scheduler as scheduler_module
from vinted_anuncios.shared.models import Mode
from vinted_anuncios.shared.settings import load_settings

LOGGER = logging.getLogger("test-scheduler")


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
        self.jobs: list[Job] = []
        self.started = False

    def add_job(
        self,
        func: Callable[..., None],
        trigger: object,
        *,
        kwargs: dict[str, object],
        id: str,
        max_instances: int,
        coalesce: bool,
    ) -> None:
        self.jobs.append(Job(func, trigger, kwargs, id, max_instances, coalesce))

    def start(self) -> None:
        self.started = True


def test_start_registra_un_solo_job_de_publicacion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeScheduler(timezone=object())
    monkeypatch.setattr(scheduler_module, "BlockingScheduler", lambda timezone: fake)

    calls: list[dict[str, object]] = []
    monkeypatch.setattr(scheduler_module, "run_publish", lambda **kwargs: calls.append(kwargs))

    settings = load_settings({"DATA_DIR": str(tmp_path), "REPLY_CRON": "*/5 * * * *"})
    scheduler_module.start(settings, Mode.DRY_RUN, logger=LOGGER)

    assert fake.started is True
    assert [job.id for job in fake.jobs] == ["publicacion_diaria"]
    job = fake.jobs[0]
    assert job.max_instances == 1 and job.coalesce is True
    assert "hour='16'" in str(job.trigger)
    assert "minute='0'" in str(job.trigger)

    job.func(**job.kwargs)
    assert calls == [{"settings": settings, "mode": Mode.DRY_RUN, "logger": LOGGER}]


def test_start_no_usa_reply_cron(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeScheduler(timezone=object())
    monkeypatch.setattr(scheduler_module, "BlockingScheduler", lambda timezone: fake)
    monkeypatch.setattr(scheduler_module, "run_publish", lambda **_kwargs: None)

    settings = load_settings({"DATA_DIR": str(tmp_path), "REPLY_CRON": "no es cron"})
    scheduler_module.start(settings, Mode.DRY_RUN, logger=LOGGER)

    assert fake.started is True
    assert [job.id for job in fake.jobs] == ["publicacion_diaria"]
