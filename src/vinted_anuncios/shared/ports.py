from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from .models import FavoriteScanResult, Listing, PublishResult


class ElementPort(Protocol):
    """Parte de un elemento del DOM que usan los adapters de Vinted."""

    @property
    def text(self) -> str: ...

    def clear(self) -> None: ...

    def send_keys(self, *value: str) -> None: ...

    def click(self) -> None: ...

    def get_attribute(self, name: str) -> str | None: ...

    def find_element(self, by: str, value: str) -> ElementPort: ...


class DriverPort(Protocol):
    """Interfaz mínima del navegador; el runner no conoce Selenium."""

    def get(self, url: str) -> None: ...

    def find_element(self, by: str, value: str) -> ElementPort: ...

    def find_elements(self, by: str, value: str) -> Sequence[ElementPort]: ...

    @property
    def current_url(self) -> str: ...

    @property
    def current_window_handle(self) -> str: ...

    @property
    def window_handles(self) -> Sequence[str]: ...

    def execute_script(self, script: str, *args: object) -> object: ...

    def switch_to_window(self, handle: str) -> None: ...

    def close(self) -> None: ...

    def quit(self) -> None: ...


class ListingPublisher(Protocol):
    def publish(self, listing: Listing) -> PublishResult: ...


class FavoriteReplier(Protocol):
    def scan_favorites(self, template: str | None) -> FavoriteScanResult: ...


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

    def release(self, account: str) -> None:
        """Cierra la sesión de una cuenta cuando termina su último trabajo."""

    def close(self) -> None: ...


Logger = logging.Logger
