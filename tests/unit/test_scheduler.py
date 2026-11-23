from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from vinted_anuncios import scheduler as scheduler_module
from vinted_anuncios.shared.models import Mode
from vinted_anuncios.shared.settings import SettingsError, load_settings

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


class LockRecorder:
    def __init__(self) -> None:
        self.entered = 0
        self.exited = 0

    def __enter__(self) -> None:
        self.entered += 1

    def __exit__(self, *_args: object) -> None:
        self.exited += 1


def test_start_registra_dos_jobs_y_usa_el_bloqueo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeScheduler(timezone=object())
    lock = LockRecorder()
    monkeypatch.setattr(scheduler_module, "BlockingScheduler", lambda timezone: fake)
    monkeypatch.setattr(scheduler_module, "Lock", lambda: lock)

    calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        scheduler_module, "run_publish", lambda **kwargs: calls.append(("publish", kwargs))
    )
    monkeypatch.setattr(
        scheduler_module, "run_reply", lambda **kwargs: calls.append(("reply", kwargs))
    )

    settings = load_settings({"DATA_DIR": str(tmp_path), "REPLY_CRON": "*/5 * * * *"})
    scheduler_module.start(settings, Mode.DRY_RUN, logger=LOGGER)

    assert fake.started is True
    assert [job.id for job in fake.jobs] == ["publicacion_diaria", "respuesta_favoritos"]
    assert all(job.max_instances == 1 and job.coalesce is True for job in fake.jobs)
    assert "hour='16'" in str(fake.jobs[0].trigger)
    assert "minute='0'" in str(fake.jobs[0].trigger)
    assert "minute='*/5'" in str(fake.jobs[1].trigger)

    for job in fake.jobs:
        job.func(**job.kwargs)

    assert [name for name, _ in calls] == ["publish", "reply"]
    assert lock.entered == 2
    assert lock.exited == 2


def test_start_rechaza_cron_invalido(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeScheduler(timezone=object())
    monkeypatch.setattr(scheduler_module, "BlockingScheduler", lambda timezone: fake)

    settings = load_settings({"DATA_DIR": str(tmp_path), "REPLY_CRON": "no es cron"})
    with pytest.raises(SettingsError, match="REPLY_CRON"):
        scheduler_module.start(settings, Mode.DRY_RUN, logger=LOGGER)

    assert not fake.jobs
