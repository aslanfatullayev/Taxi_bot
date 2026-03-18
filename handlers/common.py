"""
Common handlers: /start command and role detection.

Role detection logic:
  - If the user's Telegram ID is in DRIVER_IDS → driver
  - Otherwise → client
"""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import DRIVER_IDS
from keyboards.client_kb import client_main_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user_id = message.from_user.id

    if user_id in DRIVER_IDS:
        await message.answer(
            "👋 Привет, водитель!\n"
            "Ожидайте новые заказы — они придут автоматически."
        )
    else:
        await message.answer(
            "👋 Привет! Я бот для вызова такси.\n"
            "Нажмите кнопку ниже, чтобы заказать поездку.",
            reply_markup=client_main_kb(),
        )
