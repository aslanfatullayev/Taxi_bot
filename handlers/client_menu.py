"""
Client menu section handlers:
  - 👤 Мой профиль
  - ❓ Помощь (with complaint flow)
  - 🚗 Я водитель (route to registration or active driver)
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from config import ADMIN_IDS
from db import AsyncSessionLocal
from keyboards.client_kb import client_main_kb, help_kb, cancel_inline_kb
from services import client_service, driver_service
from states.client import ComplaintFSM

router = Router()


# ── 👤 My Profile ──────────────────────────────────────────────────────────
@router.message(F.text == "👤 Мой профиль")
async def my_profile(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is not None:
        await message.answer(
            "⚠️ Сначала завершите текущее действие.\n"
            "Нажмите '❌ Отмена', чтобы прервать его."
        )
        return

    async with AsyncSessionLocal() as session:
        client = await client_service.get_client_by_user_id(session, message.from_user.id)

    if not client:
        await message.answer(
            "❌ Вы не зарегистрированы.\nОтправьте /start для регистрации."
        )
        return

    await message.answer(
        f"👤 <b>Мой профиль</b>\n\n"
        f"🏷 <b>Имя:</b> {client.name}\n"
        f"📞 <b>Телефон:</b> {client.phone}\n"
        f"🆔 <b>Telegram ID:</b> <code>{client.user_id}</code>",
        parse_mode="HTML",
        reply_markup=client_main_kb(),
    )


# ── ❓ Help ─────────────────────────────────────────────────────────────────
@router.message(F.text == "❓ Помощь")
async def help_section(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is not None:
        await message.answer(
            "⚠️ Сначала завершите текущее действие.\nНажмите '❌ Отмена', чтобы прервать."
        )
        return

    await message.answer(
        "❓ <b>Помощь</b>\n\n"
        "Если у вас возникли проблемы, вы можете подать жалобу на водителя.",
        parse_mode="HTML",
        reply_markup=help_kb(),
    )


# ── Complaint flow ──────────────────────────────────────────────────────────
@router.callback_query(F.data == "help_complaint")
async def complaint_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ComplaintFSM.waiting_driver_name)
    await callback.message.edit_text(
        "📛 <b>Жалоба на водителя</b>\n\n"
        "Шаг 1/3: Введите <b>имя водителя</b> (как вы его знаете):",
        parse_mode="HTML",
        reply_markup=cancel_inline_kb(),
    )


@router.message(ComplaintFSM.waiting_driver_name)
async def complaint_driver_name(message: Message, state: FSMContext) -> None:
    await state.update_data(driver_name=message.text)
    await state.set_state(ComplaintFSM.waiting_driver_phone)
    await message.answer(
        "Шаг 2/3: Введите <b>номер телефона водителя</b>:",
        parse_mode="HTML",
        reply_markup=cancel_inline_kb(),
    )


@router.message(ComplaintFSM.waiting_driver_phone)
async def complaint_driver_phone(message: Message, state: FSMContext) -> None:
    await state.update_data(driver_phone=message.text)
    await state.set_state(ComplaintFSM.waiting_reason)
    await message.answer(
        "Шаг 3/3: Опишите <b>причину жалобы</b> подробно:",
        parse_mode="HTML",
        reply_markup=cancel_inline_kb(),
    )


@router.message(ComplaintFSM.waiting_reason)
async def complaint_reason(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    user = message.from_user
    complaint_text = (
        f"🚨 <b>Новая жалоба!</b>\n\n"
        f"<b>От клиента:</b> {user.full_name} (@{user.username or 'нет'}) "
        f"[ID: <code>{user.id}</code>]\n\n"
        f"🚗 <b>Водитель (имя):</b> {data['driver_name']}\n"
        f"📞 <b>Телефон водителя:</b> {data['driver_phone']}\n\n"
        f"📝 <b>Причина жалобы:</b>\n{message.text}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                chat_id=admin_id,
                text=complaint_text,
                parse_mode="HTML",
            )
        except Exception as e:
            print(f"Failed to send complaint to admin {admin_id}: {e}")

    await message.answer(
        "✅ Ваша жалоба успешно отправлена администратору.\n"
        "Мы рассмотрим её в ближайшее время.",
        reply_markup=client_main_kb(),
    )


@router.callback_query(F.data == "help_cancel")
async def complaint_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Жалоба отменена.")
    await callback.message.answer("Вы вернулись в главное меню.", reply_markup=client_main_kb())


# ── 🚗 "Я водитель" section ────────────────────────────────────────────────
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def driver_section_kb(is_registered: bool) -> InlineKeyboardMarkup:
    if is_registered:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Продолжить работу", callback_data="driver_go_online")],
            [InlineKeyboardButton(text="👤 Профиль водителя", callback_data="driver_view_profile")],
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Стать водителем", callback_data="driver_register")],
        ])


@router.message(F.text == "🚗 Я водитель")
async def driver_section(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is not None:
        await message.answer(
            "⚠️ Сначала завершите текущее действие.\nНажмите '❌ Отмена', чтобы прервать."
        )
        return

    async with AsyncSessionLocal() as session:
        driver = await driver_service.get_driver_by_user_id(session, message.from_user.id)

    if driver and driver.is_active:
        from models.driver import DriverStatus
        status_label = {
            DriverStatus.IDLE: "🟢 Свободен",
            DriverStatus.BUSY: "🔴 В поездке",
            DriverStatus.OFFLINE: "⚫ Оффлайн",
        }.get(driver.status, driver.status)

        await message.answer(
            f"🚗 <b>Профиль водителя</b>\n\n"
            f"👤 <b>Имя:</b> {driver.name}\n"
            f"📞 <b>Телефон:</b> {driver.phone}\n"
            f"🚘 <b>Авто:</b> {driver.car_model} ({driver.car_number})\n"
            f"📊 <b>Статус:</b> {status_label}",
            parse_mode="HTML",
            reply_markup=driver_section_kb(is_registered=True),
        )
    else:
        await message.answer(
            "🚗 <b>Стать водителем</b>\n\n"
            "Вы ещё не зарегистрированы как водитель.\n"
            "Нажмите кнопку ниже, чтобы подать заявку.",
            parse_mode="HTML",
            reply_markup=driver_section_kb(is_registered=False),
        )


@router.callback_query(F.data == "driver_register")
async def driver_register_via_button(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.delete()
    from states.driver_registration import DriverRegistrationFSM
    await state.set_state(DriverRegistrationFSM.waiting_name)
    await callback.message.answer(
        "👤 Введите ваше полное имя:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.callback_query(F.data == "driver_view_profile")
async def driver_view_profile(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        driver = await driver_service.get_driver_by_user_id(session, callback.from_user.id)

    if not driver:
        await callback.answer("Профиль не найден.", show_alert=True)
        return

    from models.driver import DriverStatus
    status_label = {
        DriverStatus.IDLE: "🟢 Свободен",
        DriverStatus.BUSY: "🔴 В поездке",
        DriverStatus.OFFLINE: "⚫ Оффлайн",
    }.get(driver.status, driver.status)

    await callback.message.edit_text(
        f"🚗 <b>Профиль водителя</b>\n\n"
        f"👤 <b>Имя:</b> {driver.name}\n"
        f"📞 <b>Телефон:</b> {driver.phone}\n"
        f"🚘 <b>Авто:</b> {driver.car_model} ({driver.car_number})\n"
        f"📊 <b>Статус:</b> {status_label}",
        parse_mode="HTML",
        reply_markup=driver_section_kb(is_registered=True),
    )


@router.callback_query(F.data == "driver_go_online")
async def driver_go_online_cb(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        await driver_service.set_driver_status(
            session, callback.from_user.id, "idle"
        )
    await callback.answer("✅ Вы снова на линии!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=driver_section_kb(is_registered=True))
