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
    """Elige los adapters reales o de simulación según el modo."""

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
            FilesystemListingStore() if mode is Mode.PUBLISH else NoOpListingStore()
        )
        self._drivers: dict[str, DriverPort] = {}
        if mode is Mode.PUBLISH:
            for account in accounts:
                self._drivers[account] = self._factory.create(account)

    @property
    def store(self) -> ListingStore:
        return self._store

    def publisher_for(self, account: str) -> ListingPublisher:
        if self._mode is Mode.DRY_RUN:
            return DryRunListingPublisher()
        return VintedListingPublisher(self._drivers[account], self._settings, self._logger)

    def replier_for(self, account: str) -> FavoriteReplier:
        if self._mode is Mode.DRY_RUN:
            return DryRunFavoriteReplier(self._logger)
        return VintedFavoriteReplier(self._drivers[account], self._settings, self._logger)

    def close(self) -> None:
        for driver in self._drivers.values():
            self._factory.close(driver)
