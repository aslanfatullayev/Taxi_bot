from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from locales import t


def language_select_kb() -> ReplyKeyboardMarkup:
    """Language selection keyboard shown before anything else."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇺🇿 O'zbek")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def client_main_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Main menu keyboard for clients (4 buttons)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_order_taxi", lang)), KeyboardButton(text=t("btn_i_am_driver", lang))],
            [KeyboardButton(text=t("btn_my_profile", lang)), KeyboardButton(text=t("btn_help", lang))],
        ],
        resize_keyboard=True,
    )


def confirm_order_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_confirm", lang))],
            [KeyboardButton(text=t("btn_cancel", lang))],
        ],
        resize_keyboard=True,
    )


def location_request_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_send_location", lang), request_location=True)],
            [KeyboardButton(text=t("btn_type_address", lang))],
            [KeyboardButton(text=t("btn_cancel", lang))],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def help_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_complaint", lang), callback_data="help_complaint")],
        ]
    )


def cancel_inline_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_cancel_inline", lang), callback_data="help_cancel")]
        ]
    )


def change_lang_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_change_lang", lang), callback_data="client_change_lang")]
        ]
    )


def client_cancel_order_kb(order_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_cancel_order", lang), callback_data=f"client_cancel_order:{order_id}")]
        ]
    )

