from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def accept_order_kb(order_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard sent to drivers with a new order."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data=f"accept_order:{order_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_order:{order_id}",
                )
            ]
        ]
    )


def rejected_order_kb() -> InlineKeyboardMarkup:
    """Keyboard shown when a driver rejects an order."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔍 Продолжить поиск",
                    callback_data="continue_search",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📴 Завершить работу",
                    callback_data="go_offline",
                )
            ]
        ]
    )


def driver_active_kb(order_id: int) -> InlineKeyboardMarkup:
    """Keyboard shown to driver after accepting an order."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Закончить поездку",
                    callback_data=f"complete_trip:{order_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📴 Закончить работу",
                    callback_data="go_offline",
                )
            ],
        ]
    )
