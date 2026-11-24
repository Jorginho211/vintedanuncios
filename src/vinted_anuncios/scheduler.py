from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .features.run_sweep.handler import run_publish
from .shared.models import Mode
from .shared.settings import Settings

PUBLISH_CRONTAB = "0 16 * * *"


def start(settings: Settings, mode: Mode, *, logger: logging.Logger) -> None:
    """Mantiene el proceso vivo con el job de publicación diaria."""
    publish_trigger = CronTrigger.from_crontab(PUBLISH_CRONTAB, timezone=settings.timezone)

    scheduler = BlockingScheduler(timezone=settings.timezone)
    scheduler.add_job(
        run_publish,
        publish_trigger,
        kwargs={"settings": settings, "mode": mode, "logger": logger},
        id="publicacion_diaria",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
