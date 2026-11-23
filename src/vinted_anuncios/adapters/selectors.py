"""Selectores y textos de Vinted centralizados.

Los selectores son provisionales: `docs/checklist.md` indica cómo validarlos
contra la web real. cambiarlos aquí evita tocar la lógica de publicación.
"""

from __future__ import annotations

HOME_URL = "https://www.vinted.es"
SELL_URL = "https://www.vinted.es/sell"
MESSAGES_URL = "https://www.vinted.es/messages"
NOTIFICATIONS_URL = "https://www.vinted.es/notifications"

SELECTOR_SELL_LINK = "[data-vinted='sell-link']"
SELECTOR_TITLE = "[data-vinted-field='title']"
SELECTOR_DESCRIPTION = "[data-vinted-field='description']"
SELECTOR_PRICE = "[data-vinted-field='price']"
SELECTOR_BRAND = "[data-vinted-field='brand']"
SELECTOR_MODEL = "[data-vinted-field='model']"
SELECTOR_CATEGORY = "[data-vinted-field='category']"
SELECTOR_PHOTO_INPUT = "[data-vinted-field='photos']"
SELECTOR_SUBMIT = "[data-vinted='publish']"
SELECTOR_SUCCESS = "[data-vinted='publish-success']"

SELECTOR_NOTIFICATION = "[data-vinted='notification']"
SELECTOR_CONVERSATION = "[data-vinted='conversation']"
SELECTOR_MESSAGE_OUT = "[data-vinted='message-out']"
SELECTOR_MESSAGE_INPUT = "[data-vinted-field='message']"
SELECTOR_SEND = "[data-vinted='send-message']"

FAVORITE_TEXT = "ha marcado como favorito tu artículo"
