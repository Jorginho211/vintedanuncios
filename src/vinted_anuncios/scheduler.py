from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .features.run_sweep.handler import run_sweep
from .shared.models import Mode
from .shared.settings import Settings


def start(settings: Settings, mode: Mode, *, logger: logging.Logger) -> None:
    """Mantiene el proceso vivo y lanza el barrido a las 16:00 locales."""
    scheduler = BlockingScheduler(timezone=settings.timezone)
    trigger = CronTrigger.from_crontab("0 16 * * *", timezone=settings.timezone)
    scheduler.add_job(
        run_sweep,
        trigger,
        kwargs={"settings": settings, "mode": mode, "logger": logger},
        id="barrido_diario",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
