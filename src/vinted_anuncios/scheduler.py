from __future__ import annotations

import logging
from collections.abc import Callable
from threading import Lock

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .features.run_sweep.handler import run_publish, run_reply
from .shared.models import Mode
from .shared.settings import Settings, SettingsError

PUBLISH_CRONTAB = "0 16 * * *"


def start(settings: Settings, mode: Mode, *, logger: logging.Logger) -> None:
    """Mantiene el proceso vivo con dos jobs que nunca usan el mismo perfil a la vez."""
    publish_trigger = CronTrigger.from_crontab(PUBLISH_CRONTAB, timezone=settings.timezone)
    try:
        reply_trigger = CronTrigger.from_crontab(settings.reply_cron, timezone=settings.timezone)
    except ValueError as exc:
        raise SettingsError(f"REPLY_CRON no es válida: {settings.reply_cron!r}") from exc

    scheduler = BlockingScheduler(timezone=settings.timezone)
    lock = Lock()

    def locked(action: Callable[..., None]) -> Callable[..., None]:
        def wrapped(**kwargs: object) -> None:
            with lock:
                action(**kwargs)

        return wrapped

    kwargs = {"settings": settings, "mode": mode, "logger": logger}
    scheduler.add_job(
        locked(run_publish),
        publish_trigger,
        kwargs=kwargs,
        id="publicacion_diaria",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        locked(run_reply),
        reply_trigger,
        kwargs=kwargs,
        id="respuesta_favoritos",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
