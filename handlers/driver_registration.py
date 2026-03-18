"""
Driver registration handler — multi-step FSM.

Flow:
  Button "🚗 Хочу стать водителем"
    → name → phone → car_model → car_number → saved to DB
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from db import AsyncSessionLocal
from services import driver_service
from states.driver_registration import DriverRegistrationFSM

router = Router()


# NOTE: Driver registration is now initiated via the "🚗 Я водитель" button
# in client_menu.py (driver_register callback). This file only contains the FSM steps.

# ── Step 2: Name ───────────────────────────────────────────────────────────
@router.message(DriverRegistrationFSM.waiting_name)
async def get_driver_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(DriverRegistrationFSM.waiting_phone)
    await message.answer("📞 Введите ваш номер телефона:\nПример: +998901234567")


# ── Step 3: Phone ──────────────────────────────────────────────────────────
@router.message(DriverRegistrationFSM.waiting_phone)
async def get_driver_phone(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.text)
    await state.set_state(DriverRegistrationFSM.waiting_car_model)
    await message.answer("🚗 Введите марку и модель автомобиля:\nПример: KIA K5")


# ── Step 4: Car model ──────────────────────────────────────────────────────
@router.message(DriverRegistrationFSM.waiting_car_model)
async def get_driver_car_model(message: Message, state: FSMContext) -> None:
    await state.update_data(car_model=message.text)
    await state.set_state(DriverRegistrationFSM.waiting_car_number)
    await message.answer("🔢 Введите номер автомобиля:\nПример: 01 A 123 BA")


# ── Step 5: Car number → send to Admin ─────────────────────────────────────
@router.message(DriverRegistrationFSM.waiting_car_number)
async def get_driver_car_number(message: Message, state: FSMContext) -> None:
    from config import ADMIN_IDS
    from keyboards.admin_kb import admin_approve_kb
    from services import admin_service

    await state.update_data(car_number=message.text)
    data = await state.get_data()
    await state.clear()

    user_id = message.from_user.id
    username = message.from_user.username or "без_юзернейма"
    user_data = {
        "name": data["name"],
        "phone": data["phone"],
        "car_model": data["car_model"],
        "car_number": data["car_number"],
    }

    # Store in memory for admin approval
    admin_service.add_pending_driver(user_id, user_data)

    # Notify user
    await message.answer(
        "⏳ Ваша заявка отправлена администратору на проверку.\n"
        "Ожидайте ответа..."
    )

    # Send to all admins
    admin_text = (
        f"🚨 <b>Новая заявка в водители!</b>\n\n"
        f"<b>ID:</b> <code>{user_id}</code>\n"
        f"<b>Username:</b> @{username}\n\n"
        f"👤 <b>Имя:</b> {user_data['name']}\n"
        f"📞 <b>Телефон:</b> {user_data['phone']}\n"
        f"🚗 <b>Авто:</b> {user_data['car_model']}\n"
        f"🔢 <b>Номер:</b> {user_data['car_number']}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                reply_markup=admin_approve_kb(user_id),
                parse_mode="HTML",
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление админу {admin_id}: {e}")

