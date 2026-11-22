from __future__ import annotations

import time


def pause(seconds: float) -> None:
    """Pausa opcional entre acciones, configurada en ``Settings``."""
    if seconds > 0:
        time.sleep(seconds)
