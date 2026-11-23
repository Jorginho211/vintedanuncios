from __future__ import annotations

import logging

from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By

from ..shared.models import ReplyResult
from ..shared.pause import ActionPacer
from ..shared.ports import DriverPort
from ..shared.settings import Settings
from . import selectors
from .vinted_wait import click_css, fill, wait_for_all


class VintedFavoriteReplier:
    """Responde una vez a los avisos de favorito con un driver real."""

    def __init__(self, driver: DriverPort, settings: Settings, logger: logging.Logger) -> None:
        self._driver = driver
        self._settings = settings
        self._logger = logger
        self._pacer = ActionPacer(settings.action_delay_min, settings.action_delay_max)

    def _pace(self) -> None:
        self._pacer.pause()

    def reply(self, template: str) -> ReplyResult:
        timeout = self._settings.wait_seconds
        driver = self._driver
        replied: list[str] = []
        errors: list[str] = []
        try:
            driver.get(selectors.NOTIFICATIONS_URL)
            self._pace()
            notices = wait_for_all(driver, selectors.SELECTOR_NOTIFICATION, timeout)
            favorites = [
                notice for notice in notices if selectors.FAVORITE_TEXT in notice.text.lower()
            ]

            for index, notice in enumerate(favorites):
                try:
                    notice.click()
                    self._pace()
                    conversations = driver.find_elements(
                        By.CSS_SELECTOR, selectors.SELECTOR_CONVERSATION
                    )
                    if not conversations:
                        continue
                    if driver.find_elements(By.CSS_SELECTOR, selectors.SELECTOR_MESSAGE_OUT):
                        continue

                    conversation_id = (
                        conversations[0].get_attribute("data-conversation-id") or "desconocido"
                    )
                    fill(driver, selectors.SELECTOR_MESSAGE_INPUT, template, timeout)
                    self._pace()
                    click_css(driver, selectors.SELECTOR_SEND, timeout)
                    self._pace()
                    replied.append(conversation_id)
                except (NoSuchElementException, TimeoutException, WebDriverException) as exc:
                    errors.append(f"aviso {index}: {exc}")
        except (NoSuchElementException, TimeoutException, WebDriverException) as exc:
            errors.append(f"fallo al revisar avisos: {exc}")

        return ReplyResult(replied=tuple(replied), errors=tuple(errors))
