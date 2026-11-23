"""Selectores y textos de Vinted centralizados.

Los selectores de publicación se validaron contra el DOM real de CuentaA en
`/tmp/opencode/vinted_*.html` (volcados de la fase 1 del plan 016). Los de
favoritos siguen siendo provisionales y se validan con `docs/checklist.md`.
"""

from __future__ import annotations

HOME_URL = "https://www.vinted.es"
SELL_URL = "https://www.vinted.es/items/new"
MESSAGES_URL = "https://www.vinted.es/messages"
NOTIFICATIONS_URL = "https://www.vinted.es/notifications"

SELECTOR_SELL_LINK = 'a[href="/items/new"]'
SELECTOR_COOKIES = "#accept-recommended-btn-handler"
SELECTOR_PHOTO_INPUT = '[data-testid="add-photos-input"]'
SELECTOR_UPLOAD_LOADER = '[data-testid="upload-button-loader"]'
SELECTOR_UPLOAD_ERROR = '[data-testid="item-upload-critical-error-dialog"]'
SELECTOR_TITLE = "#title"
SELECTOR_DESCRIPTION = "#description"
SELECTOR_PRICE = "#price"
SELECTOR_CATEGORY = '[data-testid="catalog-select-dropdown-input"]'
SELECTOR_CATEGORY_SEARCH = "#catalog-search-input"
SELECTOR_CATEGORY_OPTION = (
    '[data-testid="catalog-select-dropdown-content"] '
    '[role="radio"][id^="catalog-search-"][id$="-result"]'
)
SELECTOR_BRAND = '[data-testid="brand-select-dropdown-input"]'
SELECTOR_BRAND_SEARCH = "#brand-search-input"
SELECTOR_BRAND_OPTION = '[data-testid="brand-select-dropdown-content"] [role="radio"][id^="brand-"]'
SELECTOR_COLOR = '[data-testid="color-select-dropdown-input"]'
SELECTOR_CONDITION = '[data-testid="category-condition-single-list-input"]'
SELECTOR_CONDITION_GOOD = "#condition-2"
# El radio está oculto; Vinted reacciona al clic en la celda visible.
SELECTOR_PACKAGE_SMALL = '[data-testid="1-package-size--cell"]'
SELECTOR_SUBMIT = '[data-testid="upload-form-save-button"]'
SELECTOR_UNSAVED_DIALOG = ".ReactModal__Overlay"

# Los grupos de color se identifican por su etiqueta, no por testids internos.
XPATH_COLOR_SUGGESTION = (
    "//div[@role='group' and @aria-labelledby='color-suggestions-label']"
    "//div[@role='checkbox'][1]"
)
XPATH_COLOR_FIRST = (
    "//div[@role='group' and @aria-labelledby='color-list-label']" "//div[@role='checkbox'][1]"
)
XPATH_DISCARD_CHANGES = (
    "//button[contains(normalize-space(.),'Descartar') "
    "or contains(normalize-space(.),'No guardar') "
    "or contains(normalize-space(.),'Salir sin guardar')]"
)

SELECTOR_NOTIFICATION = "[data-vinted='notification']"
SELECTOR_CONVERSATION = "[data-vinted='conversation']"
SELECTOR_MESSAGE_OUT = "[data-vinted='message-out']"
SELECTOR_MESSAGE_INPUT = "[data-vinted-field='message']"
SELECTOR_SEND = "[data-vinted='send-message']"

FAVORITE_TEXT = "ha marcado como favorito tu artículo"
