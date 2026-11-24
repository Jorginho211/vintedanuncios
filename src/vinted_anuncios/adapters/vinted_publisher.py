from __future__ import annotations

import logging
from pathlib import Path
from typing import cast

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    UnexpectedAlertPresentException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from ..shared.models import Listing, PublishResult
from ..shared.pause import ActionPacer
from ..shared.ports import DriverPort, ElementPort
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
    scroll_next_page,
    send_keys_css,
    wait_for,
    wait_for_all,
    wait_until_gone,
)

# Marca usada en el formulario cuando la caption no especifica ninguna.
DEFAULT_BRAND = "Vintage Dressing"
# Tope de pasos al recorrer el desplegable: la lista de marcas no es infinita.
MAX_BRAND_SCROLL_STEPS = 60


class VintedListingPublisher:
    """Rellena el formulario real de Vinted; ``submit=False`` solo lo simula."""

    def __init__(
        self,
        driver: DriverPort,
        settings: Settings,
        logger: logging.Logger,
        *,
        submit: bool = True,
        check_submit: bool = False,
    ) -> None:
        self._driver = driver
        self._settings = settings
        self._logger = logger
        # El diagnóstico gana siempre: nunca debe combinarse con un clic real.
        self._check_submit = check_submit
        self._submit = submit and not check_submit
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
                message = "publicado"
            elif self._check_submit:
                self._check_submit_form()
                self._leave_form()
                message = "diagnóstico (sin pulsar Subir)"
            else:
                self._leave_form()
                message = "simulado (sin pulsar Subir)"
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
        if self._normalized_brand(brand) == self._normalized_brand(DEFAULT_BRAND):
            self._choose_default_brand_by_scroll()
            return
        self._choose_from_search(
            field=selectors.SELECTOR_BRAND,
            search=selectors.SELECTOR_BRAND_SEARCH,
            option=selectors.SELECTOR_BRAND_OPTION,
            value=brand,
        )

    def _choose_default_brand_by_scroll(self) -> None:
        """El buscador no ofrece esta marca: se recorre el listado completo."""
        self._step(f"marca {DEFAULT_BRAND!r}: desplazar listado")
        driver = self._driver
        timeout = self._settings.wait_seconds
        wanted = self._normalized_brand(DEFAULT_BRAND)
        click_css(driver, selectors.SELECTOR_BRAND, timeout)
        self._pace()
        for _ in range(MAX_BRAND_SCROLL_STEPS):
            options = retry_on_stale(
                lambda: wait_for_all(driver, selectors.SELECTOR_BRAND_OPTION, timeout)
            )
            if any(self._normalized_brand(option.text) == wanted for option in options):
                self._logger.debug("Marca %s encontrada en el listado", DEFAULT_BRAND)
                self._click_brand_option(wanted, timeout)
                self._pace()
                return
            if not scroll_next_page(driver, selectors.SELECTOR_BRAND_OPTION):
                break
            self._pace()
        raise RuntimeError(f"Vinted no ofreció la marca {DEFAULT_BRAND!r} tras recorrer el listado")

    def _click_brand_option(self, wanted: str, timeout: float) -> None:
        """Pulsa la opción coincidente; reconsultarla tolera re-renders de Vinted."""

        def attempt() -> None:
            options = wait_for_all(self._driver, selectors.SELECTOR_BRAND_OPTION, timeout)
            for option in options:
                if self._normalized_brand(option.text) == wanted:
                    click_js(self._driver, option)
                    return
            raise NoSuchElementException(f"La marca {wanted!r} desapareció del listado")

        retry_on_stale(attempt)

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

    @staticmethod
    def _safe_attribute(element: ElementPort, name: str) -> str:
        try:
            value = element.get_attribute(name)
        except (StaleElementReferenceException, WebDriverException):
            return "<no legible>"
        return value if isinstance(value, str) else "<ausente>"

    def _option_label(self, option: ElementPort) -> str:
        """Vinted expone la etiqueta en `aria-label`; el texto es el respaldo."""
        label = self._safe_attribute(option, "aria-label")
        if label in ("<ausente>", "<no legible>"):
            label = ""
        return label.strip() or str(option.text).strip()

    def _size_value(self) -> str:
        elements = self._driver.find_elements(By.CSS_SELECTOR, selectors.SELECTOR_SIZE)
        return self._safe_attribute(elements[0], "value") if elements else "<ausente>"

    def _describe_size_options(self) -> str:
        options = self._driver.find_elements(By.CSS_SELECTOR, selectors.SELECTOR_SIZE_OPTION_ANY)
        labels = [self._option_label(option) for option in options[:20]]
        return f"{len(options)} opciones en el desplegable: {labels}"

    def _size_confirmation(self, size: str, clicked: ElementPort | None) -> tuple[bool | None, str]:
        """Devuelve confirmación, rechazo o «sin señal» y el detalle visto.

        Vinted mantiene `value=""` en el campo de talla incluso tras elegir una
        opción, así que `aria-checked` manda; el valor del campo es solo respaldo.
        """
        value = self._size_value()
        if value not in ("<ausente>", "<no legible>") and matches_vinted_size(size, value):
            return True, f"campo={value!r}"

        for option in self._driver.find_elements(By.CSS_SELECTOR, selectors.SELECTOR_SIZE_OPTION):
            checked = self._safe_attribute(option, "aria-checked").casefold()
            if checked != "true":
                continue
            label = self._option_label(option)
            if matches_vinted_size(size, label):
                return True, f"opción={label!r} aria-checked=true"
            return False, f"Vinted marcó {label!r} en lugar de {size!r}"

        if clicked is not None:
            checked = self._safe_attribute(clicked, "aria-checked").casefold()
            if checked == "true":
                return True, f"opción {size!r} aria-checked=true"
            if checked == "false":
                return False, f"la opción {size!r} sigue aria-checked=false"

        return None, f"sin señal de confirmación; campo={value!r}; {self._describe_size_options()}"

    def _confirm_size(self, size: str, timeout: float, clicked: ElementPort) -> None:
        def has_signal(_driver: WebDriver) -> object:
            confirmed, _ = retry_on_stale(lambda: self._size_confirmation(size, clicked))
            return confirmed is not None or None

        try:
            WebDriverWait(cast(WebDriver, self._driver), timeout).until(has_signal)
        except TimeoutException as exc:
            confirmed, detail = self._size_confirmation(size, clicked)
            if confirmed is False:
                raise RuntimeError(f"Vinted no guardó la talla {size!r}; {detail}") from exc
            self._logger.warning("No se pudo confirmar la talla %s: %s", size, detail)
            return

        confirmed, detail = self._size_confirmation(size, clicked)
        if confirmed is False:
            raise RuntimeError(f"Vinted no guardó la talla {size!r}; {detail}")
        self._logger.debug("Talla %s confirmada: %s", size, detail)

    def _choose_size(self, size: str) -> None:
        driver = self._driver
        timeout = self._settings.wait_seconds
        self._step(f"talla {size!r}: abrir desplegable")
        try:
            click_css(driver, selectors.SELECTOR_SIZE, timeout)
        except TimeoutException as exc:
            found = len(driver.find_elements(By.CSS_SELECTOR, selectors.SELECTOR_SIZE))
            raise RuntimeError(
                f"no se abrió el campo de talla {selectors.SELECTOR_SIZE!r} ({found} campos)"
            ) from exc
        self._pace()

        self._step(f"talla {size!r}: buscar opción")

        def attempt() -> None:
            try:
                options = wait_for_all(driver, selectors.SELECTOR_SIZE_OPTION, timeout)
            except TimeoutException as exc:
                raise RuntimeError(
                    f"no aparecieron opciones con {selectors.SELECTOR_SIZE_OPTION!r}; "
                    f"{self._describe_size_options()}"
                ) from exc
            for option in options:
                label = self._option_label(option)
                if matches_vinted_size(size, label):
                    self._step(f"talla {size!r}: elegir opción")
                    self._logger.debug("Talla %s: opción elegida %s", size, label)
                    click_js(driver, option)
                    self._pace()
                    self._confirm_size(size, timeout, option)
                    return
            raise RuntimeError(
                f"Vinted no ofreció la talla {size!r}; {self._describe_size_options()}"
            )

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

    def _current_url(self) -> str:
        try:
            return str(cast(WebDriver, self._driver).current_url)
        except WebDriverException:
            return "<no disponible>"

    def _submit_button_state(self) -> str:
        buttons = self._driver.find_elements(By.CSS_SELECTOR, selectors.SELECTOR_SUBMIT)
        if not buttons:
            return f"sin botón {selectors.SELECTOR_SUBMIT}"
        button = buttons[0]
        return (
            f"botón {selectors.SELECTOR_SUBMIT}: "
            f"disabled={self._safe_attribute(button, 'disabled')!r}, "
            f"aria-disabled={self._safe_attribute(button, 'aria-disabled')!r}, "
            f"class={self._safe_attribute(button, 'class')!r}"
        )

    def _form_state(self) -> str:
        fields = (
            ("título", selectors.SELECTOR_TITLE),
            ("descripción", selectors.SELECTOR_DESCRIPTION),
            ("precio", selectors.SELECTOR_PRICE),
            ("categoría", selectors.SELECTOR_CATEGORY),
            ("marca", selectors.SELECTOR_BRAND),
            ("talla", selectors.SELECTOR_SIZE),
        )
        parts: list[str] = []
        for name, css in fields:
            elements = self._driver.find_elements(By.CSS_SELECTOR, css)
            value = self._safe_attribute(elements[0], "value") if elements else "<ausente>"
            parts.append(f"{name}={value!r}")
        parts.append(self._submit_button_state())
        parts.append(f"URL={self._current_url()}")
        return "; ".join(parts)

    def _visible_form_errors(self) -> str:
        errors = self._driver.find_elements(By.CSS_SELECTOR, selectors.SELECTOR_UPLOAD_ERROR)
        texts = [str(element.text).strip() for element in errors]
        return f"; errores de Vinted={texts!r}" if any(texts) else ""

    def _check_submit_form(self) -> None:
        self._step("diagnóstico antes de Subir")
        state = self._form_state()
        self._logger.info("Estado del formulario antes de «Subir»: %s", state)
        buttons = self._driver.find_elements(By.CSS_SELECTOR, selectors.SELECTOR_SUBMIT)
        if not buttons:
            raise RuntimeError(f"no aparece el botón «Subir»: {state}")
        # En HTML, `disabled=""` también deshabilita: basta con que exista.
        disabled = self._safe_attribute(buttons[0], "disabled")
        aria_disabled = self._safe_attribute(buttons[0], "aria-disabled").casefold()
        if disabled != "<ausente>" or aria_disabled == "true":
            raise RuntimeError(f"«Subir» está deshabilitado: {state}")

    def _submit_form(self) -> None:
        driver = self._driver
        self._step("Subir: pulsar")
        try:
            click_css(driver, selectors.SELECTOR_SUBMIT, self._settings.wait_seconds)
        except TimeoutException as exc:
            raise RuntimeError(
                f"no se pudo pulsar «Subir»: {self._submit_button_state()}; {self._form_state()}"
            ) from exc
        self._pace()
        self._step("Subir: esperar navegación")
        try:
            WebDriverWait(cast(WebDriver, driver), 30).until(
                lambda d: "/items/new" not in d.current_url
            )
        except TimeoutException as exc:
            raise RuntimeError(
                f"«Subir» pulsado pero Vinted no navegó: URL={self._current_url()}; "
                f"{self._form_state()}{self._visible_form_errors()}"
            ) from exc

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
