from __future__ import annotations

from dataclasses import dataclass


class SessionError(ValueError):
    """El nombre no identifica un perfil Firefox existente."""


@dataclass(frozen=True, slots=True)
class CheckSession:
    session: str
