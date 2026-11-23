from __future__ import annotations

import logging

from ...adapters.filesystem import FilesystemListingStore
from ...adapters.selenium_driver import SeleniumDriverFactory
from ...adapters.vinted_publisher import VintedListingPublisher
from ...adapters.vinted_replier import VintedFavoriteReplier
from ...shared.models import Mode
from ...shared.ports import DriverPort, FavoriteReplier, ListingPublisher, ListingStore
from ...shared.settings import Settings
from ..publish_listings.dry_run import DryRunListingPublisher
from ..reply_favorites.dry_run import DryRunFavoriteReplier
from .noop_store import NoOpListingStore


class SeleniumRuntime:
    """Elige los adapters reales o de simulación según el modo.

    Los drivers se abren solo cuando una cuenta tiene trabajo y se cierran en
    cuanto termina esa cuenta: publicación y favoritos nunca comparten sesión.
    """

    def __init__(
        self,
        settings: Settings,
        mode: Mode,
        accounts: tuple[str, ...],
        logger: logging.Logger,
    ) -> None:
        self._settings = settings
        self._mode = mode
        self._logger = logger
        self._factory = SeleniumDriverFactory(settings)
        self._store: ListingStore = (
            FilesystemListingStore(settings.data_dir)
            if mode in (Mode.PUBLISH, Mode.SIMULATE_SEND)
            else NoOpListingStore()
        )
        self._drivers: dict[str, DriverPort] = {}
        self._accounts = accounts

    @property
    def store(self) -> ListingStore:
        return self._store

    def _driver_for(self, account: str) -> DriverPort:
        if account not in self._drivers:
            self._drivers[account] = self._factory.create(account)
        return self._drivers[account]

    def publisher_for(self, account: str) -> ListingPublisher:
        if self._mode is Mode.DRY_RUN:
            return DryRunListingPublisher()
        return VintedListingPublisher(
            self._driver_for(account),
            self._settings,
            self._logger,
            submit=self._mode is Mode.PUBLISH,
        )

    def replier_for(self, account: str) -> FavoriteReplier:
        if self._mode in (Mode.DRY_RUN, Mode.SIMULATE_SEND):
            return DryRunFavoriteReplier(self._logger)
        return VintedFavoriteReplier(self._driver_for(account), self._settings, self._logger)

    def release(self, account: str) -> None:
        driver = self._drivers.pop(account, None)
        if driver is not None:
            self._factory.close(driver)

    def close(self) -> None:
        for account in tuple(self._drivers):
            self.release(account)
