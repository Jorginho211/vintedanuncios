from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from .models import Listing, PublishResult, ReplyResult


class ElementPort(Protocol):
    """Parte de un elemento del DOM que usan los adapters de Vinted."""

    @property
    def text(self) -> str: ...

    def clear(self) -> None: ...

    def send_keys(self, *value: str) -> None: ...

    def click(self) -> None: ...

    def get_attribute(self, name: str) -> str | None: ...


class DriverPort(Protocol):
    """Interfaz mínima del navegador; el runner no conoce Selenium."""

    def get(self, url: str) -> None: ...

    def find_element(self, by: str, value: str) -> ElementPort: ...

    def find_elements(self, by: str, value: str) -> Sequence[ElementPort]: ...

    def quit(self) -> None: ...


class ListingPublisher(Protocol):
    def publish(self, listing: Listing) -> PublishResult: ...


class FavoriteReplier(Protocol):
    def reply(self, template: str) -> ReplyResult: ...


class ListingStore(Protocol):
    def delete(self, folder: Path) -> bool:
        """Borra la carpeta y devuelve si se borró realmente."""


class DriverFactory(Protocol):
    def create(self, account: str) -> DriverPort: ...

    def close(self, driver: DriverPort) -> None: ...


class Runtime(Protocol):
    """Puertos ya elegidos para el modo de ejecución."""

    @property
    def store(self) -> ListingStore: ...

    def publisher_for(self, account: str) -> ListingPublisher: ...

    def replier_for(self, account: str) -> FavoriteReplier: ...

    def close(self) -> None: ...


Logger = logging.Logger
