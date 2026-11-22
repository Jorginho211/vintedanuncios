from __future__ import annotations

import logging

from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

from ..shared.models import Listing, PublishResult
from ..shared.ports import DriverPort
from ..shared.settings import Settings
from . import selectors
from .vinted_wait import fill, fill_optional, wait_for, wait_for_clickable


class VintedListingPublisher:
    """Rellena el formulario de publicación de Vinted con un driver real."""

    def __init__(self, driver: DriverPort, settings: Settings, logger: logging.Logger) -> None:
        self._driver = driver
        self._settings = settings
        self._logger = logger

    def publish(self, listing: Listing) -> PublishResult:
        timeout = self._settings.wait_seconds
        driver = self._driver
        try:
            driver.get(selectors.SELL_URL)
            fill(driver, selectors.SELECTOR_TITLE, listing.title, timeout)
            fill(driver, selectors.SELECTOR_DESCRIPTION, listing.description, timeout)
            fill(driver, selectors.SELECTOR_PRICE, f"{listing.caption.price:g}", timeout)
            fill_optional(
                driver, selectors.SELECTOR_BRAND, listing.caption.brand, timeout, self._logger
            )
            # El destino del modelo en Vinted está pendiente de confirmar: se intenta
            # en el campo propio y, si no existe, se omite sin fallar.
            fill_optional(
                driver, selectors.SELECTOR_MODEL, listing.caption.model, timeout, self._logger
            )
            fill(driver, selectors.SELECTOR_CATEGORY, listing.category, timeout)

            photo_input = wait_for(driver, selectors.SELECTOR_PHOTO_INPUT, timeout)
            for image in listing.images:
                photo_input.send_keys(str(image))

            submit = wait_for_clickable(driver, selectors.SELECTOR_SUBMIT, timeout)
            submit.click()
            wait_for(driver, selectors.SELECTOR_SUCCESS, 30)
            return PublishResult(ok=True, message="publicado")
        except (NoSuchElementException, TimeoutException, WebDriverException) as exc:
            return PublishResult(ok=False, message=f"fallo al publicar: {exc}")
