from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def client_main_kb() -> ReplyKeyboardMarkup:
    """Main menu keyboard for clients."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚖 Заказать такси")],
            [KeyboardButton(text="🚗 Хочу стать водителем")],
        ],
        resize_keyboard=True,
    )


def confirm_order_kb() -> ReplyKeyboardMarkup:
    """Confirmation keyboard shown before placing an order."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Подтвердить")],
            [KeyboardButton(text="❌ Отменить")],
        ],
        resize_keyboard=True,
    )


def location_request_kb() -> ReplyKeyboardMarkup:
    """Keyboard with geolocation button + manual input option."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
            [KeyboardButton(text="✏️ Написать адрес вручную")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
