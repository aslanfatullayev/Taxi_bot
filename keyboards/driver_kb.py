from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def accept_order_kb(order_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard sent to drivers with a new order."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять заказ",
                    callback_data=f"accept_order:{order_id}",
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
