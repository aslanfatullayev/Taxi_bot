"""
Client menu section handlers (bilingual):
  - 👤 Мой профиль / Mening profilim
  - ❓ Помощь / Yordam (with complaint flow)
  - 🚗 Я водитель / Men haydovchiman
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from config import ADMIN_IDS
from db import AsyncSessionLocal
from keyboards.client_kb import client_main_kb, help_kb, cancel_inline_kb, change_lang_kb
from locales import t
from services import client_service, driver_service
from states.client import ComplaintFSM

router = Router()


async def _get_lang(user_id: int) -> str:
    async with AsyncSessionLocal() as session:
        client = await client_service.get_client_by_user_id(session, user_id)
    return client.lang if client else "ru"


# ── 👤 My Profile ──────────────────────────────────────────────────────────
@router.message(F.text.in_({"👤 Мой профиль", "👤 Mening profilim"}))
async def my_profile(message: Message, state: FSMContext) -> None:
    lang = await _get_lang(message.from_user.id)
    current_state = await state.get_state()
    if current_state is not None:
        await message.answer(t("state_guard", lang))
        return

    async with AsyncSessionLocal() as session:
        client = await client_service.get_client_by_user_id(session, message.from_user.id)

    if not client:
        await message.answer(t("not_registered", lang))
        return

    await message.answer(
        t("profile_title", lang).format(
            name=client.name, phone=client.phone, user_id=client.user_id
        ),
        parse_mode="HTML",
        reply_markup=change_lang_kb(lang),
    )


# ── 🌐 Change Language ──────────────────────────────────────────────────────
@router.callback_query(F.data == "client_change_lang")
async def client_change_lang(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await _get_lang(callback.from_user.id)
    new_lang = "uz" if lang == "ru" else "ru"

    async with AsyncSessionLocal() as session:
        await client_service.update_client_lang(session, callback.from_user.id, new_lang)
        client = await client_service.get_client_by_user_id(session, callback.from_user.id)

    # Refresh Profile message with new language
    await callback.message.edit_text(
        t("profile_title", new_lang).format(
            name=client.name, phone=client.phone, user_id=client.user_id
        ),
        parse_mode="HTML",
        reply_markup=change_lang_kb(new_lang),
    )
    
    # Notify user and update ReplyKeyboard
    await callback.message.answer(
        t("lang_changed", new_lang),
        reply_markup=client_main_kb(new_lang)
    )
    await callback.answer()


# ── ❓ Help ─────────────────────────────────────────────────────────────────
@router.message(F.text.in_({"❓ Помощь", "❓ Yordam"}))
async def help_section(message: Message, state: FSMContext) -> None:
    lang = await _get_lang(message.from_user.id)
    current_state = await state.get_state()
    if current_state is not None:
        await message.answer(t("state_guard", lang))
        return

    await message.answer(
        t("help_title", lang),
        parse_mode="HTML",
        reply_markup=help_kb(lang),
    )


# ── Complaint flow ──────────────────────────────────────────────────────────
@router.callback_query(F.data == "help_complaint")
async def complaint_start(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await _get_lang(callback.from_user.id)
    await state.set_state(ComplaintFSM.waiting_driver_name)
    await state.update_data(lang=lang)
    await callback.message.edit_text(
        t("complaint_step1", lang),
        parse_mode="HTML",
        reply_markup=cancel_inline_kb(lang),
    )


@router.message(ComplaintFSM.waiting_driver_name)
async def complaint_driver_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await state.update_data(driver_name=message.text)
    await state.set_state(ComplaintFSM.waiting_driver_phone)
    await message.answer(t("complaint_step2", lang), parse_mode="HTML", reply_markup=cancel_inline_kb(lang))


@router.message(ComplaintFSM.waiting_driver_phone)
async def complaint_driver_phone(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await state.update_data(driver_phone=message.text)
    await state.set_state(ComplaintFSM.waiting_reason)
    await message.answer(t("complaint_step3", lang), parse_mode="HTML", reply_markup=cancel_inline_kb(lang))


@router.message(ComplaintFSM.waiting_reason)
async def complaint_reason(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await state.clear()

    user = message.from_user
    complaint_text = (
        f"🚨 <b>Yangi shikoyat / Новая жалоба!</b>\n\n"
        f"<b>От:</b> {user.full_name} (@{user.username or 'нет'}) "
        f"[ID: <code>{user.id}</code>]\n\n"
        f"🚗 <b>Водитель (имя):</b> {data['driver_name']}\n"
        f"📞 <b>Телефон водителя:</b> {data['driver_phone']}\n\n"
        f"📝 <b>Причина:</b>\n{message.text}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(chat_id=admin_id, text=complaint_text, parse_mode="HTML")
        except Exception as e:
            print(f"Failed to send complaint to admin {admin_id}: {e}")

    await message.answer(t("complaint_sent", lang), reply_markup=client_main_kb(lang))


@router.callback_query(F.data == "help_cancel")
async def complaint_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", await _get_lang(callback.from_user.id))
    await state.clear()
    await callback.message.edit_text(t("complaint_cancelled", lang))
    await callback.message.answer(t("back_to_menu", lang), reply_markup=client_main_kb(lang))


# ── 🚗 Driver section ──────────────────────────────────────────────────────
def driver_section_kb(is_registered: bool, is_online: bool = False, lang: str = "ru") -> InlineKeyboardMarkup:
    if is_registered:
        toggle_btn = InlineKeyboardButton(
            text=t("btn_go_offline" if is_online else "btn_go_online", lang),
            callback_data="driver_go_offline_menu" if is_online else "driver_go_online",
        )
        return InlineKeyboardMarkup(inline_keyboard=[
            [toggle_btn],
            [InlineKeyboardButton(text=t("btn_driver_profile", lang), callback_data="driver_view_profile")],
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_become_driver", lang), callback_data="driver_register")],
        ])


def _status_label(status: str, lang: str) -> str:
    from models.driver import DriverStatus
    mapping = {
        DriverStatus.IDLE: t("driver_status_idle", lang),
        DriverStatus.BUSY: t("driver_status_busy", lang),
        DriverStatus.OFFLINE: t("driver_status_offline", lang),
    }
    return mapping.get(status, status)


@router.message(F.text.in_({"🚗 Я водитель", "🚗 Men haydovchiman"}))
async def driver_section(message: Message, state: FSMContext) -> None:
    lang = await _get_lang(message.from_user.id)
    current_state = await state.get_state()
    if current_state is not None:
        await message.answer(t("state_guard", lang))
        return

    async with AsyncSessionLocal() as session:
        driver = await driver_service.get_driver_by_user_id(session, message.from_user.id)

    if driver and driver.is_active:
        from models.driver import DriverStatus
        is_online = driver.status in (DriverStatus.IDLE, DriverStatus.BUSY)
        await message.answer(
            t("driver_profile_title", lang).format(
                name=driver.name, phone=driver.phone,
                car_model=driver.car_model, car_number=driver.car_number,
                status=_status_label(driver.status, lang),
            ),
            parse_mode="HTML",
            reply_markup=driver_section_kb(is_registered=True, is_online=is_online, lang=lang),
        )
    else:
        await message.answer(
            t("driver_not_registered", lang),
            parse_mode="HTML",
            reply_markup=driver_section_kb(is_registered=False, lang=lang),
        )


@router.callback_query(F.data == "driver_register")
async def driver_register_via_button(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await _get_lang(callback.from_user.id)
    await callback.message.delete()
    from states.driver_registration import DriverRegistrationFSM
    await state.set_state(DriverRegistrationFSM.waiting_name)
    await state.update_data(lang=lang)
    await callback.message.answer(t("dreg_ask_name", lang), reply_markup=ReplyKeyboardRemove())


@router.callback_query(F.data == "driver_view_profile")
async def driver_view_profile(callback: CallbackQuery) -> None:
    lang = await _get_lang(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        driver = await driver_service.get_driver_by_user_id(session, callback.from_user.id)

    if not driver:
        await callback.answer(t("not_registered", lang), show_alert=True)
        return

    from models.driver import DriverStatus
    is_online = driver.status in (DriverStatus.IDLE, DriverStatus.BUSY)
    await callback.message.edit_text(
        t("driver_profile_title", lang).format(
            name=driver.name, phone=driver.phone,
            car_model=driver.car_model, car_number=driver.car_number,
            status=_status_label(driver.status, lang),
        ),
        parse_mode="HTML",
        reply_markup=driver_section_kb(is_registered=True, is_online=is_online, lang=lang),
    )


@router.callback_query(F.data == "driver_go_online")
async def driver_go_online_cb(callback: CallbackQuery) -> None:
    lang = await _get_lang(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        driver = await driver_service.get_driver_by_user_id(session, callback.from_user.id)
        await driver_service.set_driver_status(session, callback.from_user.id, "idle")

    if not driver:
        await callback.answer(t("not_registered", lang), show_alert=True)
        return

    await callback.message.edit_text(
        t("driver_profile_title", lang).format(
            name=driver.name, phone=driver.phone,
            car_model=driver.car_model, car_number=driver.car_number,
            status=t("driver_status_idle", lang),
        ),
        parse_mode="HTML",
        reply_markup=driver_section_kb(is_registered=True, is_online=True, lang=lang),
    )
    await callback.answer("✅ " + t("driver_status_idle", lang))


@router.callback_query(F.data == "driver_go_offline_menu")
async def driver_go_offline_menu_cb(callback: CallbackQuery) -> None:
    lang = await _get_lang(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        driver = await driver_service.get_driver_by_user_id(session, callback.from_user.id)
        await driver_service.set_driver_status(session, callback.from_user.id, "offline")

    if not driver:
        await callback.answer(t("not_registered", lang), show_alert=True)
        return

    await callback.message.edit_text(
        t("driver_profile_title", lang).format(
            name=driver.name, phone=driver.phone,
            car_model=driver.car_model, car_number=driver.car_number,
            status=t("driver_status_offline", lang),
        ),
        parse_mode="HTML",
        reply_markup=driver_section_kb(is_registered=True, is_online=False, lang=lang),
    )
    await callback.answer("⚫ " + t("driver_status_offline", lang))
