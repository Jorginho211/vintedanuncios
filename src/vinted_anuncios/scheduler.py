from __future__ import annotations

import logging
import random
from collections.abc import Callable
from datetime import datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from .features.run_sweep.handler import run_publish, run_reply
from .shared.models import Mode
from .shared.settings import Settings

PUBLISH_CRONTAB = "0 16 * * *"
REPLY_MIN_MINUTES = 30
REPLY_MAX_MINUTES = 60
REPLY_JOB_ID = "respuesta_favoritos"


def _reply_delay_minutes(randint: Callable[[int, int], int] = random.randint) -> int:
    return randint(REPLY_MIN_MINUTES, REPLY_MAX_MINUTES)


def _next_reply_run(
    *,
    now: datetime,
    randint: Callable[[int, int], int] = random.randint,
) -> datetime:
    return now + timedelta(minutes=_reply_delay_minutes(randint))


def start(
    settings: Settings,
    mode: Mode,
    *,
    logger: logging.Logger,
    scheduler: BlockingScheduler | None = None,
    randint: Callable[[int, int], int] = random.randint,
    now: Callable[[], datetime] | None = None,
) -> None:
    """Mantiene el proceso vivo con jobs de publicación y de inspección de favoritos."""

    clock = now or (lambda: datetime.now(settings.timezone))
    active_scheduler = scheduler or BlockingScheduler(timezone=settings.timezone)

    def schedule_reply() -> None:
        next_run = _next_reply_run(now=clock(), randint=randint)
        trigger = DateTrigger(run_date=next_run, timezone=settings.timezone)
        if active_scheduler.get_job(REPLY_JOB_ID) is None:
            active_scheduler.add_job(
                run_reply_job,
                trigger,
                id=REPLY_JOB_ID,
                max_instances=1,
                coalesce=True,
            )
        else:
            active_scheduler.reschedule_job(REPLY_JOB_ID, trigger=trigger)
        logger.info("Próxima inspección de favoritos: %s", next_run.isoformat())

    def run_reply_job() -> None:
        try:
            run_reply(settings, mode, logger=logger)
        finally:
            schedule_reply()

    publish_trigger = CronTrigger.from_crontab(PUBLISH_CRONTAB, timezone=settings.timezone)
    active_scheduler.add_job(
        run_publish,
        publish_trigger,
        kwargs={"settings": settings, "mode": mode, "logger": logger},
        id="publicacion_diaria",
        max_instances=1,
        coalesce=True,
    )
    schedule_reply()
    active_scheduler.start()
