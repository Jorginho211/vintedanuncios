from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import TypeVar, cast

from selenium.common.exceptions import (
    NoAlertPresentException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..shared.ports import DriverPort, ElementPort

T = TypeVar("T")


def retry_on_stale(action: Callable[[], T], attempts: int = 3) -> T:
    """Repite una acción si Vinted sustituye el nodo justo antes de usarla."""
    for attempt in range(attempts):
        try:
            return action()
        except StaleElementReferenceException:
            if attempt == attempts - 1:
                raise
    raise AssertionError("retry_on_stale sin intentos")


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


def wait_until_gone(driver: DriverPort, css: str, timeout: float) -> None:
    _wait(driver, timeout).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, css)))


def click_js(driver: DriverPort, element: ElementPort) -> None:
    """Pulsa por JavaScript: Vinted interpone overlays que bloquean `click()`."""
    cast(WebDriver, driver).execute_script("arguments[0].click()", element)


def scroll_next_page(driver: DriverPort, css: str) -> bool:
    """Desplaza el ancestro con scroll de `css`; devuelve si `scrollTop` avanzó."""
    script = """
    var node = document.querySelector(arguments[0]);
    if (!node) { return false; }
    while (node && node.scrollHeight <= node.clientHeight) {
        node = node.parentElement;
    }
    if (!node) { return false; }
    var before = node.scrollTop;
    node.scrollTop = before + Math.max(node.clientHeight * 0.9, 200);
    return node.scrollTop > before;
    """
    return bool(cast(WebDriver, driver).execute_script(script, css))


def click_css(driver: DriverPort, css: str, timeout: float, *, clickable: bool = True) -> None:
    """Busca y pulsa en un solo intento, repitiendo si el nodo queda obsoleto."""

    def attempt() -> None:
        element = (
            wait_for_clickable(driver, css, timeout)
            if clickable
            else wait_for(driver, css, timeout)
        )
        click_js(driver, element)

    retry_on_stale(attempt)


def click_xpath(driver: DriverPort, xpath: str, timeout: float) -> None:
    """Igual que `click_css` para los grupos de color y el diálogo de descarte."""

    def attempt() -> None:
        element = _wait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        click_js(driver, cast(ElementPort, element))

    retry_on_stale(attempt)


def go_back(driver: DriverPort) -> None:
    cast(WebDriver, driver).back()


def accept_alert(driver: DriverPort) -> bool:
    """Acepta el diálogo nativo de «cambios sin guardar», si aparece."""
    try:
        cast(WebDriver, driver).switch_to.alert.accept()
    except NoAlertPresentException:
        return False
    return True


def fill(driver: DriverPort, css: str, value: str, timeout: float) -> None:
    def attempt() -> None:
        element = wait_for(driver, css, timeout)
        element.clear()
        element.send_keys(value)

    retry_on_stale(attempt)


def send_keys_css(driver: DriverPort, css: str, value: str, timeout: float) -> None:
    """Escribe en un campo (por ejemplo el input de fotos) tolerando re-renders."""

    def attempt() -> None:
        wait_for(driver, css, timeout).send_keys(value)

    retry_on_stale(attempt)


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
