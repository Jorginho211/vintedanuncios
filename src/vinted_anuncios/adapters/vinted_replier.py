from __future__ import annotations

import logging
import random
from collections.abc import Sequence
from dataclasses import dataclass

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ..shared import offers
from ..shared.models import FavoriteNotification, FavoriteScanResult
from ..shared.offers import OfferPriceError
from ..shared.pause import ActionPacer
from ..shared.ports import DriverPort, ElementPort
from ..shared.settings import Settings
from . import selectors
from .vinted_wait import (
    click_css,
    close_current_tab,
    fill,
    open_tab,
    scroll_window,
    send_keys_css,
    wait_for,
    wait_for_all,
    wait_for_page_ready,
)

MAX_FAVORITE_NOTIFICATIONS = 40
MAX_SCROLL_ATTEMPTS = 12


@dataclass(frozen=True, slots=True)
class _FavoriteTarget:
    url: str
    notification_id: str


def _notification_id(element: ElementPort, index: int) -> str:
    for attribute in ("data-notification-id", "id", "href"):
        value = element.get_attribute(attribute)
        if value:
            return value
    return f"wrapper-{index}"


def _target_url(element: ElementPort, driver: DriverPort) -> str:
    href = element.get_attribute("href")
    if isinstance(href, str) and href:
        return href
    try:
        link = element.find_element(By.CSS_SELECTOR, "a[href]")
        link_href = link.get_attribute("href")
        if isinstance(link_href, str) and link_href:
            return link_href
    except Exception:  # noqa: BLE001 - el wrapper puede no tener enlace directo
        pass
    return driver.current_url


class VintedFavoriteReplier:
    """Responde a favoritos no contestados con un driver real."""

    def __init__(
        self,
        driver: DriverPort,
        settings: Settings,
        logger: logging.Logger,
        account: str = "",
        *,
        send: bool = False,
    ) -> None:
        self._driver = driver
        self._settings = settings
        self._logger = logger
        self._account = account
        self._send = send
        self._pacer = ActionPacer(settings.action_delay_min, settings.action_delay_max)

    def _pace(self) -> None:
        self._pacer.pause()

    def _pause(self, minimum: float, maximum: float) -> None:
        delay_min = max(self._settings.action_delay_min, minimum)
        delay_max = max(self._settings.action_delay_max, maximum)
        if delay_max < delay_min:
            delay_max = delay_min
        ActionPacer(delay_min, delay_max).pause()

    def _collect_favorites(self, driver: DriverPort) -> list[_FavoriteTarget]:
        seen: set[str] = set()
        targets: list[_FavoriteTarget] = []
        stagnant = 0

        for _ in range(MAX_SCROLL_ATTEMPTS):
            wrappers: Sequence[ElementPort] = ()
            try:
                wrappers = driver.find_elements(
                    By.CSS_SELECTOR, selectors.SELECTOR_NOTIFICATION_WRAPPER
                )
            except (NoSuchElementException, TimeoutException, WebDriverException) as exc:
                self._logger.debug("No se pudieron leer notificaciones: %s", exc)

            found_before = len(targets)
            for index, wrapper in enumerate(wrappers):
                text = wrapper.text.casefold()
                if selectors.FAVORITE_NOTIFICATION_TEXT not in text:
                    continue
                url = _target_url(wrapper, driver)
                notification_id = _notification_id(wrapper, index)
                key = url or notification_id
                if key in seen:
                    continue
                seen.add(key)
                targets.append(_FavoriteTarget(url=url, notification_id=notification_id))
                if len(targets) >= MAX_FAVORITE_NOTIFICATIONS:
                    return targets

            if len(targets) == found_before:
                stagnant += 1
            else:
                stagnant = 0
            if stagnant >= 2:
                break
            self._pause(0.8, 1.8)
            if not scroll_window(driver, amount=float(random.randint(260, 520))):
                stagnant += 1
                if stagnant >= 2:
                    break
            self._pause(1.2, 2.6)

        return targets

    def _is_replied(self, timeout: float) -> bool:
        try:
            wait_for(self._driver, selectors.SELECTOR_REPLIED_MARKER, timeout)
            return True
        except TimeoutException:
            return False

    def _offer_and_message(
        self, notification_id: str, template: str | None
    ) -> tuple[str | None, str | None, bool, str | None]:
        """Devuelve precio anterior, precio ofertado, envío y error opcional."""
        timeout = self._settings.wait_seconds
        try:
            price_input = wait_for(self._driver, selectors.SELECTOR_OFFER_PRICE_INPUT, timeout)
            previous = offers.parse_previous_price(price_input.get_attribute("placeholder"))
        except (OfferPriceError, NoSuchElementException, TimeoutException) as exc:
            return None, None, False, f"notificación {notification_id}: {exc}"

        previous_price = offers.format_price(previous)
        offered_price = offers.format_price(previous - offers.DISCOUNT)

        if not self._send:
            self._logger.info(
                "[%s] En %s se ofrecería %s y se enviaría la plantilla",
                self._account,
                notification_id,
                offered_price,
            )
            return previous_price, offered_price, False, None

        if template is None:
            return (
                previous_price,
                offered_price,
                False,
                f"notificación {notification_id}: falta la plantilla de respuesta",
            )

        try:
            self._pace()
            fill(self._driver, selectors.SELECTOR_OFFER_PRICE_INPUT, offered_price, timeout)
            self._pace()
            click_css(self._driver, selectors.SELECTOR_OFFER_SUBMIT, timeout)
            self._pace()
            send_keys_css(self._driver, selectors.SELECTOR_COMPOSER_INPUT, template, timeout)
            self._pace()
            send_keys_css(self._driver, selectors.SELECTOR_COMPOSER_INPUT, Keys.ENTER, timeout)
            self._pace()
        except (NoSuchElementException, TimeoutException, WebDriverException) as exc:
            return (
                previous_price,
                offered_price,
                False,
                f"notificación {notification_id}: fallo al responder ({exc})",
            )
        return previous_price, offered_price, True, None

    def scan_favorites(self, template: str | None) -> FavoriteScanResult:
        timeout = self._settings.wait_seconds
        driver = self._driver
        notifications: list[FavoriteNotification] = []
        errors: list[str] = []
        stopped_reason = "no_more"

        try:
            driver.get(selectors.MEMBER_NOTIFICATIONS_URL)
            self._pace()
            try:
                wait_for_page_ready(driver, timeout)
            except TimeoutException:
                self._logger.debug("La página de notificaciones tardó en quedar lista")
            self._pause(1.0, 2.2)
            try:
                wait_for_all(driver, selectors.SELECTOR_NOTIFICATION_WRAPPER, timeout)
            except TimeoutException:
                self._logger.info("No se encontraron wrappers de notificación")
                return FavoriteScanResult((), "no_more", ())

            targets = self._collect_favorites(driver)
            self._logger.info("Encontrados %s favoritos para responder", len(targets))
            main_handle = driver.current_window_handle

            for target in targets:
                tab_handle: str | None = None
                try:
                    self._pause(0.8, 1.6)
                    tab_handle = open_tab(driver, target.url)
                    self._pace()
                    try:
                        wait_for_page_ready(driver, timeout)
                    except TimeoutException:
                        self._logger.debug(
                            "La notificación %s tardó en quedar lista", target.notification_id
                        )
                    self._pause(1.2, 2.8)

                    # Esperar a que salga la modal del precio antes de determinar si esta cargado
                    wait_for(self._driver, selectors.SELECTOR_OFFER_PRICE_INPUT, timeout)

                    if self._is_replied(timeout):
                        notifications.append(
                            FavoriteNotification(
                                account=self._account,
                                url=target.url,
                                notification_id=target.notification_id,
                                replied=True,
                            )
                        )
                        stopped_reason = "replied_found"
                        self._logger.info(
                            "Detectada conversación respondida en %s; se detiene el barrido",
                            target.notification_id,
                        )
                        break

                    previous_price, offered_price, sent, error = self._offer_and_message(
                        target.notification_id, template
                    )
                    if error is not None:
                        errors.append(error)
                    notifications.append(
                        FavoriteNotification(
                            account=self._account,
                            url=target.url,
                            notification_id=target.notification_id,
                            replied=False,
                            previous_price=previous_price,
                            offered_price=offered_price,
                            message_sent=sent,
                        )
                    )
                except (NoSuchElementException, TimeoutException, WebDriverException) as exc:
                    errors.append(f"notificación {target.notification_id}: {exc}")
                finally:
                    if tab_handle is not None:
                        try:
                            self._pause(0.6, 1.4)
                            close_current_tab(driver, main_handle)
                            self._pace()
                        except WebDriverException as exc:
                            errors.append(f"cerrar pestaña {target.notification_id}: {exc}")

            if stopped_reason != "replied_found" and len(targets) >= MAX_FAVORITE_NOTIFICATIONS:
                stopped_reason = "max_reached"

        except (NoSuchElementException, TimeoutException, WebDriverException) as exc:
            errors.append(f"fallo al revisar avisos: {exc}")
            stopped_reason = "error"

        return FavoriteScanResult(
            notifications=tuple(notifications),
            stopped_reason=stopped_reason,
            errors=tuple(errors),
        )
