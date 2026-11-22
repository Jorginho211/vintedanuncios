from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import cast

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..shared.ports import DriverPort, ElementPort


def _wait(driver: DriverPort, timeout: float) -> WebDriverWait[WebDriver]:
    # Los expected_conditions de Selenium están tipados contra WebDriver, no contra
    # nuestro puerto. El objeto real siempre es un WebDriver del adapter.
    return WebDriverWait(cast(WebDriver, driver), timeout)


def wait_for(driver: DriverPort, css: str, timeout: float) -> ElementPort:
    element = _wait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
    return cast(ElementPort, element)


def wait_for_all(driver: DriverPort, css: str, timeout: float) -> Sequence[ElementPort]:
    elements = _wait(driver, timeout).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, css))
    )
    return cast(Sequence[ElementPort], elements)


def wait_for_clickable(driver: DriverPort, css: str, timeout: float) -> ElementPort:
    element = _wait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
    return cast(ElementPort, element)


def fill(driver: DriverPort, css: str, value: str, timeout: float) -> None:
    element = wait_for(driver, css, timeout)
    element.clear()
    element.send_keys(value)


def fill_optional(
    driver: DriverPort,
    css: str,
    value: str | None,
    timeout: float,
    logger: logging.Logger,
) -> None:
    if not value:
        return
    try:
        fill(driver, css, value, timeout)
    except TimeoutException:
        logger.debug("El formulario no tiene el campo opcional %s", css)
