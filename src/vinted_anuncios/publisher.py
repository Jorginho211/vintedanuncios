from __future__ import annotations

import logging

from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import selectors
from .models import Listing, PublishResult

_WAIT_SECONDS = 15


def _wait_for(driver: WebDriver, css: str) -> WebElement:
    return WebDriverWait(driver, _WAIT_SECONDS).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css))
    )


def _fill(driver: WebDriver, css: str, value: str) -> None:
    element = _wait_for(driver, css)
    element.clear()
    element.send_keys(value)


def _fill_optional(driver: WebDriver, css: str, value: str | None, logger: logging.Logger) -> None:
    if not value:
        return
    try:
        _fill(driver, css, value)
    except TimeoutException:
        logger.debug("El formulario no tiene el campo opcional %s", css)


def publish_listing(
    driver: WebDriver | None,
    listing: Listing,
    *,
    dry_run: bool,
    logger: logging.Logger,
) -> PublishResult:
    """Rellena el formulario de Vinted. En ``dry_run`` no necesita navegador."""
    if dry_run:
        return PublishResult(ok=True, message=f"[dry-run] {listing.folder} -> {listing.title}")
    if driver is None:
        raise RuntimeError("Falta el navegador para publicar")

    try:
        driver.get(selectors.SELL_URL)
        _fill(driver, selectors.SELECTOR_TITLE, listing.title)
        _fill(driver, selectors.SELECTOR_DESCRIPTION, listing.description)
        _fill(driver, selectors.SELECTOR_PRICE, f"{listing.caption.price:g}")
        _fill_optional(driver, selectors.SELECTOR_BRAND, listing.caption.brand, logger)
        # El destino del modelo en Vinted está pendiente de confirmar: se intenta
        # en el campo propio y, si no existe, se omite sin fallar.
        _fill_optional(driver, selectors.SELECTOR_MODEL, listing.caption.model, logger)
        _fill(driver, selectors.SELECTOR_CATEGORY, listing.category)

        photo_input = _wait_for(driver, selectors.SELECTOR_PHOTO_INPUT)
        for image in listing.images:
            photo_input.send_keys(str(image))

        submit = WebDriverWait(driver, _WAIT_SECONDS).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selectors.SELECTOR_SUBMIT))
        )
        submit.click()
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selectors.SELECTOR_SUCCESS))
        )
        return PublishResult(ok=True, message="publicado")
    except (NoSuchElementException, TimeoutException, WebDriverException) as exc:
        return PublishResult(ok=False, message=f"fallo al publicar: {exc}")
