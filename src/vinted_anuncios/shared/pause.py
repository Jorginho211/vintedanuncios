from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass


def pause(seconds: float) -> None:
    """Pausa opcional entre acciones, configurada en ``Settings``."""
    if seconds > 0:
        time.sleep(seconds)


@dataclass(frozen=True, slots=True)
class ActionPacer:
    """Pausa breve entre acciones de Selenium para dar tiempo al DOM."""

    min_seconds: float
    max_seconds: float
    uniform: Callable[[float, float], float] = random.uniform
    sleep: Callable[[float], None] = time.sleep

    def pause(self) -> None:
        seconds = self.uniform(self.min_seconds, self.max_seconds)
        if seconds > 0:
            self.sleep(seconds)
