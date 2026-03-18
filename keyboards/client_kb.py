from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


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
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )


def location_request_kb() -> ReplyKeyboardMarkup:
    """Keyboard with geolocation button + manual input option."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
            [KeyboardButton(text="✏️ Написать адрес вручную")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def client_cancel_order_kb(order_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard for client to cancel an active order."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить заказ", callback_data=f"client_cancel_order:{order_id}")]
        ]
    )


def client_cancel_reason_kb() -> InlineKeyboardMarkup:
    """Inline keyboard to abort cancellation."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться", callback_data="abort_client_cancel")]
        ]
    )
