from __future__ import annotations

import os
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .runner import run_once


def start(*, publish: bool) -> None:
    """Mantiene el proceso vivo y lanza el barrido a las 16:00 locales."""
    timezone = ZoneInfo(os.getenv("TZ", "Europe/Madrid"))
    scheduler = BlockingScheduler(timezone=timezone)
    trigger = CronTrigger.from_crontab("0 16 * * *", timezone=timezone)
    scheduler.add_job(
        run_once,
        trigger,
        kwargs={"publish": publish},
        id="barrido_diario",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
