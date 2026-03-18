"""
Common handlers: /start command and role detection.

Role detection logic:
  - If the user's Telegram ID is in DRIVER_IDS → driver
  - Otherwise → client
"""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from config import DRIVER_IDS
from keyboards.client_kb import client_main_kb
from db import AsyncSessionLocal
from services import client_service
from states.client import ClientRegistrationFSM

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    await state.clear()

    if user_id in DRIVER_IDS:
        await message.answer(
            "👋 Привет, водитель!\n"
            "Ожидайте новые заказы — они придут автоматически."
        )
    else:
        # Check if client exists
        async with AsyncSessionLocal() as session:
            client = await client_service.get_client_by_user_id(session, user_id)
            
        if client:
            await message.answer(
                f"👋 Привет, {client.name}!\n"
                "Нажмите кнопку ниже, чтобы заказать поездку.",
                reply_markup=client_main_kb(),
            )
        else:
            await state.set_state(ClientRegistrationFSM.waiting_name)
            await message.answer(
                "👋 Привет! Добро пожаловать.\n\n"
                "Для вызова такси нужно пройти короткую регистрацию.\n\n"
                "👤 Введите ваше имя (как к вам обращаться):",
                reply_markup=ReplyKeyboardRemove(),
            )


@router.message(ClientRegistrationFSM.waiting_name)
async def process_client_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(ClientRegistrationFSM.waiting_phone)
    await message.answer("📞 Теперь введите ваш номер телефона (например: +998901234567):")


@router.message(ClientRegistrationFSM.waiting_phone)
async def process_client_phone(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    name = data["name"]
    phone = message.text
    
    async with AsyncSessionLocal() as session:
        await client_service.add_client(session, message.from_user.id, name, phone)
        
    await state.clear()
    await message.answer(
        f"✅ Отлично, {name}! Регистрация завершена.\n\n"
        "Теперь вы можете заказывать такси.",
        reply_markup=client_main_kb(),
    )

