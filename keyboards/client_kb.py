from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def client_main_kb() -> ReplyKeyboardMarkup:
    """Main menu keyboard for clients (4 buttons)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚖 Заказать такси"), KeyboardButton(text="🚗 Я водитель")],
            [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True,
    )


def confirm_order_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Подтвердить")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )


def location_request_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
            [KeyboardButton(text="✏️ Написать адрес вручную")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def help_kb() -> InlineKeyboardMarkup:
    """Help section keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📛 Подать жалобу", callback_data="help_complaint")],
        ]
    )


def cancel_inline_kb() -> InlineKeyboardMarkup:
    """Generic inline cancel."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="help_cancel")]
        ]
    )


def client_cancel_order_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить заказ", callback_data=f"client_cancel_order:{order_id}")]
        ]
    )


def client_cancel_reason_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться", callback_data="abort_client_cancel")]
        ]
    )

