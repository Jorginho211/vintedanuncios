from __future__ import annotations

import logging

from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import selectors
from .models import ReplyResult

_WAIT_SECONDS = 15


def reply_to_favorites(
    driver: WebDriver | None,
    template: str,
    *,
    dry_run: bool,
    logger: logging.Logger,
) -> ReplyResult:
    """Responde una vez a los favoritos. En ``dry_run`` no necesita navegador."""
    if dry_run:
        logger.info("[dry-run] Se revisarían los avisos de favorito")
        return ReplyResult(replied=(), errors=())
    if driver is None:
        raise RuntimeError("Falta el navegador para responder")

    replied: list[str] = []
    errors: list[str] = []
    try:
        driver.get(selectors.NOTIFICATIONS_URL)
        notices = WebDriverWait(driver, _WAIT_SECONDS).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selectors.SELECTOR_NOTIFICATION))
        )
        favorites = [notice for notice in notices if selectors.FAVORITE_TEXT in notice.text.lower()]

        for index, notice in enumerate(favorites):
            try:
                notice.click()
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
                field = WebDriverWait(driver, _WAIT_SECONDS).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, selectors.SELECTOR_MESSAGE_INPUT)
                    )
                )
                field.send_keys(template)
                send = WebDriverWait(driver, _WAIT_SECONDS).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selectors.SELECTOR_SEND))
                )
                send.click()
                replied.append(conversation_id)
            except (NoSuchElementException, TimeoutException, WebDriverException) as exc:
                errors.append(f"aviso {index}: {exc}")
    except (NoSuchElementException, TimeoutException, WebDriverException) as exc:
        errors.append(f"fallo al revisar avisos: {exc}")

    return ReplyResult(replied=tuple(replied), errors=tuple(errors))
