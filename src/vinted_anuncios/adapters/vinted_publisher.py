from __future__ import annotations

import logging
from pathlib import Path
from typing import cast

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    UnexpectedAlertPresentException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from ..shared.models import Listing, PublishResult
from ..shared.pause import ActionPacer
from ..shared.ports import DriverPort
from ..shared.settings import Settings
from ..shared.sizes import matches_vinted_size
from . import selectors
from .vinted_wait import (
    accept_alert,
    click_css,
    click_js,
    click_xpath,
    fill,
    go_back,
    retry_on_stale,
    send_keys_css,
    wait_for,
    wait_for_all,
    wait_until_gone,
)

# Marca usada en el formulario cuando la caption no especifica ninguna.
DEFAULT_BRAND = "Vintage Dressing"


class VintedListingPublisher:
    """Rellena el formulario real de Vinted; ``submit=False`` solo lo simula."""

    def __init__(
        self,
        driver: DriverPort,
        settings: Settings,
        logger: logging.Logger,
        *,
        submit: bool = True,
    ) -> None:
        self._driver = driver
        self._settings = settings
        self._logger = logger
        self._submit = submit
        self._step_name = "inicio"
        self._pacer = ActionPacer(settings.action_delay_min, settings.action_delay_max)

    def _step(self, name: str) -> None:
        self._step_name = name
        self._logger.debug("Paso del formulario: %s", name)

    def _pace(self) -> None:
        self._pacer.pause()

    def publish(self, listing: Listing) -> PublishResult:
        try:
            self._open_form()
            self._upload_photos(listing)
            self._fill_text(listing)
            self._choose_category(listing.form_category)
            self._ensure_brand(listing.caption.brand or DEFAULT_BRAND)
            self._choose_size(listing.size)
            self._choose_color()
            self._choose_condition()
            self._choose_shipping()
            if self._submit:
                self._submit_form()
            else:
                self._leave_form()
            message = "publicado" if self._submit else "simulado (sin pulsar Subir)"
            return PublishResult(ok=True, message=message)
        except (NoSuchElementException, TimeoutException, WebDriverException, RuntimeError) as exc:
            detail = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
            return PublishResult(
                ok=False,
                message=f"fallo en {self._step_name} ({type(exc).__name__}): {detail}",
            )

    def _open_form(self) -> None:
        driver = self._driver
        self._step("abrir home")
        driver.get(selectors.HOME_URL)
        self._pace()
        self._dismiss_cookies()
        self._step("pulsar Vender ahora")
        click_css(driver, selectors.SELECTOR_SELL_LINK, self._settings.wait_seconds)
        self._pace()
        self._step("esperar formulario de fotos")
        wait_for(driver, selectors.SELECTOR_PHOTO_INPUT, self._settings.wait_seconds)
        self._pace()
        self._dismiss_cookies()

    def _dismiss_cookies(self) -> None:
        banners = self._driver.find_elements(By.CSS_SELECTOR, selectors.SELECTOR_COOKIES)
        if banners:
            click_css(
                self._driver,
                selectors.SELECTOR_COOKIES,
                self._settings.wait_seconds,
                clickable=False,
            )
            self._pace()

    def _container_path(self, image: Path) -> str:
        try:
            relative = image.relative_to(self._settings.data_dir)
        except ValueError as exc:
            raise RuntimeError(f"La foto {image} está fuera de {self._settings.data_dir}") from exc
        return str(self._settings.selenium_data_dir / relative)

    def _upload_photos(self, listing: Listing) -> None:
        self._step("subir fotos")
        driver = self._driver
        payload = "\n".join(self._container_path(image) for image in listing.images)
        send_keys_css(driver, selectors.SELECTOR_PHOTO_INPUT, payload, self._settings.wait_seconds)
        self._pace()
        try:
            wait_until_gone(driver, selectors.SELECTOR_UPLOAD_LOADER, self._settings.wait_seconds)
        except TimeoutException:
            self._logger.debug("El indicador de subida no llegó a aparecer o a desaparecer")
        self._pace()
        if driver.find_elements(By.CSS_SELECTOR, selectors.SELECTOR_UPLOAD_ERROR):
            raise RuntimeError("Vinted rechazó las fotos; revisa que sean JPEG/PNG y no HEIC")

    def _fill_text(self, listing: Listing) -> None:
        self._step("rellenar texto")
        driver = self._driver
        timeout = self._settings.wait_seconds
        fill(driver, selectors.SELECTOR_TITLE, listing.title, timeout)
        self._pace()
        fill(driver, selectors.SELECTOR_DESCRIPTION, listing.description, timeout)
        self._pace()
        price = f"{listing.caption.price:.2f}".replace(".", ",")
        fill(driver, selectors.SELECTOR_PRICE, price, timeout)
        self._pace()

    def _choose_category(self, category: str) -> None:
        self._step(f"categoría {category!r}")
        self._choose_from_search(
            field=selectors.SELECTOR_CATEGORY,
            search=selectors.SELECTOR_CATEGORY_SEARCH,
            option=selectors.SELECTOR_CATEGORY_OPTION,
            value=category,
        )
        wait_for(
            self._driver, selectors.SELECTOR_BRAND, self._settings.wait_seconds
        )  # el formulario ya se actualizó con la categoría
        self._pace()

    @staticmethod
    def _normalized_brand(value: str) -> str:
        return "".join(char for char in value.casefold() if char.isalnum())

    def _ensure_brand(self, brand: str) -> None:
        """Vinted suele sugerir la marca desde las fotos; solo la cambia si hace falta."""
        self._step(f"marca {brand!r}")
        current = retry_on_stale(
            lambda: wait_for(
                self._driver, selectors.SELECTOR_BRAND, self._settings.wait_seconds
            ).get_attribute("value")
            or ""
        )
        if self._normalized_brand(current) == self._normalized_brand(brand):
            self._logger.debug("Vinted ya sugirió la marca %s", current)
            self._pace()
            return
        self._choose_from_search(
            field=selectors.SELECTOR_BRAND,
            search=selectors.SELECTOR_BRAND_SEARCH,
            option=selectors.SELECTOR_BRAND_OPTION,
            value=brand,
        )

    def _choose_from_search(self, *, field: str, search: str, option: str, value: str) -> None:
        driver = self._driver
        timeout = self._settings.wait_seconds
        click_css(driver, field, timeout)
        self._pace()
        fill(driver, search, value, timeout)
        self._pace()
        options = wait_for_all(driver, option, timeout)
        if not options:
            raise RuntimeError(f"Vinted no ofreció opciones para {value!r}")
        click_css(driver, option, timeout, clickable=False)
        self._pace()

    def _choose_size(self, size: str) -> None:
        self._step(f"talla {size!r}")
        driver = self._driver
        timeout = self._settings.wait_seconds
        click_css(driver, selectors.SELECTOR_SIZE, timeout)
        self._pace()

        def attempt() -> None:
            options = wait_for_all(driver, selectors.SELECTOR_SIZE_OPTION, timeout)
            for option in options:
                if matches_vinted_size(size, option.text):
                    self._logger.debug("Talla %s: opción elegida %s", size, option.text)
                    click_js(driver, option)
                    self._pace()
                    return
            raise RuntimeError(f"Vinted no ofreció la talla {size!r}")

        retry_on_stale(attempt)

    def _choose_color(self) -> None:
        self._step("color")
        driver = self._driver
        timeout = self._settings.wait_seconds
        self._step("color: abrir desplegable")
        click_css(driver, selectors.SELECTOR_COLOR, timeout)
        self._pace()
        xpath = selectors.XPATH_COLOR_SUGGESTION
        if not driver.find_elements(By.XPATH, xpath):
            self._logger.debug("Vinted no sugirió color; se toma el primero de la lista")
            xpath = selectors.XPATH_COLOR_FIRST
        if not driver.find_elements(By.XPATH, xpath):
            raise RuntimeError("Vinted no ofreció colores")
        self._step("color: elegir opción")
        click_xpath(driver, xpath, timeout)
        self._pace()

    def _choose_condition(self) -> None:
        self._step("estado")
        driver = self._driver
        timeout = self._settings.wait_seconds
        self._step("estado: abrir desplegable")
        click_css(driver, selectors.SELECTOR_CONDITION, timeout)
        self._pace()
        self._step("estado: elegir Muy bueno")
        click_css(driver, selectors.SELECTOR_CONDITION_GOOD, timeout)
        self._pace()

    def _choose_shipping(self) -> None:
        self._step("envío")
        click_css(self._driver, selectors.SELECTOR_PACKAGE_SMALL, self._settings.wait_seconds)
        self._pace()

    def _submit_form(self) -> None:
        self._step("pulsar Subir")
        driver = self._driver
        click_css(driver, selectors.SELECTOR_SUBMIT, self._settings.wait_seconds)
        self._pace()
        WebDriverWait(cast(WebDriver, driver), 30).until(
            lambda d: "/items/new" not in d.current_url
        )

    def _leave_form(self) -> None:
        self._step("volver atrás sin publicar")
        driver = self._driver
        try:
            go_back(driver)
        except UnexpectedAlertPresentException:
            self._logger.debug("Vinted mostró un diálogo nativo al volver atrás")
        self._pace()
        accept_alert(driver)
        self._pace()
        unsaved = driver.find_elements(By.XPATH, selectors.XPATH_DISCARD_CHANGES)
        if unsaved:
            click_xpath(driver, selectors.XPATH_DISCARD_CHANGES, self._settings.wait_seconds)
            self._pace()
        wait_for(driver, selectors.SELECTOR_SELL_LINK, self._settings.wait_seconds)
        self._pace()


__all__ = ["VintedListingPublisher"]
