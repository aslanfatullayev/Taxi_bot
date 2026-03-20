"""
Driver registration FSM handlers (bilingual).
Registration is initiated from client_menu.py via the 'Стать водителем' button.
"""

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from states.driver_registration import DriverRegistrationFSM
from locales import t

router = Router()


async def _lang(state: FSMContext) -> str:
    data = await state.get_data()
    return data.get("lang", "ru")


@router.message(DriverRegistrationFSM.waiting_name)
async def get_driver_name(message: Message, state: FSMContext) -> None:
    lang = await _lang(state)
    await state.update_data(name=message.text)
    await state.set_state(DriverRegistrationFSM.waiting_phone)
    await message.answer(t("dreg_ask_phone", lang))


@router.message(DriverRegistrationFSM.waiting_phone)
async def get_driver_phone(message: Message, state: FSMContext) -> None:
    lang = await _lang(state)
    await state.update_data(phone=message.text)
    await state.set_state(DriverRegistrationFSM.waiting_car_model)
    await message.answer(t("dreg_ask_car_model", lang))


@router.message(DriverRegistrationFSM.waiting_car_model)
async def get_driver_car_model(message: Message, state: FSMContext) -> None:
    lang = await _lang(state)
    await state.update_data(car_model=message.text)
    await state.set_state(DriverRegistrationFSM.waiting_car_number)
    await message.answer(t("dreg_ask_car_number", lang))


@router.message(DriverRegistrationFSM.waiting_car_number)
async def get_driver_car_number(message: Message, state: FSMContext) -> None:
    from config import ADMIN_IDS
    from keyboards.admin_kb import admin_approve_kb
    from services import admin_service

    lang = await _lang(state)
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

    admin_service.add_pending_driver(user_id, user_data)
    await message.answer(t("dreg_sent_to_admin", lang))

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
