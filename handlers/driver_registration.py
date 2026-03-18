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


# ── Step 1: Start registration ─────────────────────────────────────────────
@router.message(F.text == "🚗 Хочу стать водителем")
async def start_driver_registration(message: Message, state: FSMContext) -> None:
    await state.set_state(DriverRegistrationFSM.waiting_name)
    await message.answer(
        "👤 Введите ваше полное имя:",
        reply_markup=ReplyKeyboardRemove(),
    )


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


# ── Step 5: Car number → save to DB ────────────────────────────────────────
@router.message(DriverRegistrationFSM.waiting_car_number)
async def get_driver_car_number(message: Message, state: FSMContext) -> None:
    await state.update_data(car_number=message.text)
    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        added = await driver_service.add_driver(
            session=session,
            user_id=message.from_user.id,
            name=data["name"],
            phone=data["phone"],
            car_model=data["car_model"],
            car_number=data["car_number"],
        )

    if added:
        await message.answer(
            f"✅ Вы успешно зарегистрированы как водитель!\n\n"
            f"👤 Имя: {data['name']}\n"
            f"📞 Телефон: {data['phone']}\n"
            f"🚗 Авто: {data['car_model']}\n"
            f"🔢 Номер: {data['car_number']}\n\n"
            f"Ожидайте новые заказы!"
        )
    else:
        await message.answer(
            "ℹ️ Вы уже зарегистрированы как водитель.\n"
            "Ожидайте новые заказы!"
        )
