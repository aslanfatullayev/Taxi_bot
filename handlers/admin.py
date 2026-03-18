"""
Admin handlers:
  - approve_driver: user_id
  - reject_driver: user_id
"""

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from db import AsyncSessionLocal
from services import admin_service, driver_service

router = Router()


# ── Approve Driver ─────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("approve_driver:"))
async def approve_driver_callback(callback: CallbackQuery) -> None:
    user_id = int(callback.data.split(":")[1])
    data = admin_service.get_pending_driver(user_id)

    if not data:
        await callback.answer("⚠️ Заявка не найдена или уже обработана.", show_alert=True)
        # Update the message to show it was handled
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.edit_text(callback.message.text + "\n\n⚠️ Заявка уже обработана.")
        return

    # Add driver to DB using AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        added = await driver_service.add_driver(
            session=session,
            user_id=user_id,
            name=data["name"],
            phone=data["phone"],
            car_model=data["car_model"],
            car_number=data["car_number"],
        )

    # Remove from pending queue
    admin_service.remove_pending_driver(user_id)

    # Update admin message
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text(callback.message.text + "\n\n✅ Одобрено.")
    await callback.answer("Водитель одобрен!")

    # Notify driver
    try:
        if added:
            await callback.bot.send_message(
                chat_id=user_id,
                text="✅ Ваша заявка одобрена! Вы стали водителем 🎉\nОжидайте новые заказы.",
            )
        else:
            await callback.bot.send_message(
                chat_id=user_id,
                text="ℹ️ Ваша заявка одобрена, но вы уже были зарегистрированы как водитель.",
            )
    except Exception as e:
        print(f"Failed to notify user {user_id}: {e}")


# ── Reject Driver ──────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("reject_driver:"))
async def reject_driver_callback(callback: CallbackQuery) -> None:
    user_id = int(callback.data.split(":")[1])
    data = admin_service.get_pending_driver(user_id)

    if not data:
        await callback.answer("⚠️ Заявка не найдена или уже обработана.", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.edit_text(callback.message.text + "\n\n⚠️ Заявка уже обработана.")
        return

    # Remove from pending queue
    admin_service.remove_pending_driver(user_id)

    # Update admin message
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text(callback.message.text + "\n\n❌ Отклонено.")
    await callback.answer("Заявка отклонена.")

    # Notify driver
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text="❌ Ваша заявка на регистрацию водителя отклонена администратором.",
        )
    except Exception as e:
        print(f"Failed to notify user {user_id}: {e}")


# ── Admin Panel & Auth ───────────────────────────────────────────────────────
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS
from keyboards.admin_kb import (
    admin_panel_kb, admin_drivers_list_kb, admin_driver_manage_kb,
    admin_admins_list_kb, admin_admin_manage_kb
)
from states.admin import AdminAuthFSM, AdminChangeCodeFSM, AdminAddDriverFSM

def is_admin(user_id: int) -> bool:
    """Check if user is a main admin or authorized secondary admin."""
    return user_id in ADMIN_IDS or user_id in admin_service.SECONDARY_ADMINS


@router.message(Command("admin"))
async def admin_panel_command(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if is_admin(user_id):
        # Already authorized
        await message.answer(
            "🛠 <b>Панель администратора</b>",
            reply_markup=admin_panel_kb(is_main_admin=(user_id in ADMIN_IDS)),
            parse_mode="HTML",
        )
    else:
        # Require login code
        await state.set_state(AdminAuthFSM.waiting_code)
        await message.answer("🔒 Введите код доступа для входа в панель администратора:")


@router.message(AdminAuthFSM.waiting_code)
async def admin_auth_code(message: Message, state: FSMContext) -> None:
    if message.text == admin_service.get_admin_code():
        admin_service.SECONDARY_ADMINS.add(message.from_user.id)
        await state.clear()
        await message.answer(
            "✅ <b>Доступ разрешён!</b>\nДобро пожаловать в панель.",
            reply_markup=admin_panel_kb(is_main_admin=False),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Неверный код. Попробуйте ещё раз:")


@router.callback_query(F.data == "admin_change_code")
async def admin_change_code_start(callback: CallbackQuery, state: FSMContext) -> None:
    # Only main admins can change the code
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("У вас нет прав для этого.", show_alert=True)
        return
    await state.set_state(AdminChangeCodeFSM.waiting_new_code)
    await callback.message.edit_text("🔑 Введите новый код доступа:")


@router.message(AdminChangeCodeFSM.waiting_new_code)
async def admin_change_code_finish(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    admin_service.set_admin_code(message.text)
    await state.clear()
    await message.answer(
        f"✅ Код успешно изменён на: <code>{message.text}</code>\n"
        f"<b>Сообщите его другим администраторам!</b>",
        reply_markup=admin_panel_kb(is_main_admin=True),
        parse_mode="HTML"
    )


# ── Manage Admins ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_admins_list")
async def admin_admins_list_callback(callback: CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("У вас нет прав для этого.", show_alert=True)
        return
    
    if not admin_service.SECONDARY_ADMINS:
        await callback.answer("Нет дополнительных администраторов.", show_alert=True)
        return

    admin_data_list = []
    for uid in admin_service.SECONDARY_ADMINS:
        try:
            chat = await callback.bot.get_chat(uid)
            name = chat.first_name or f"ID: {uid}"
            admin_data_list.append({"id": uid, "name": name})
        except Exception:
            admin_data_list.append({"id": uid, "name": f"ID: {uid}"})

    await callback.message.edit_text(
        "🛡️ <b>Список дополнительных администраторов:</b>",
        reply_markup=admin_admins_list_kb(admin_data_list),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin_view_admin:"))
async def admin_view_admin_callback(callback: CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("У вас нет прав для этого.", show_alert=True)
        return
    
    target_id = int(callback.data.split(":")[1])
    if target_id not in admin_service.SECONDARY_ADMINS:
        await callback.answer("Этот пользователь больше не администратор.", show_alert=True)
        return

    text = f"🛡️ <b>Дополнительный администратор</b>\n\nID: <code>{target_id}</code>\n<i>Этот пользователь получил доступ по коду.</i>"
    try:
        user_info = await callback.bot.get_chat(target_id)
        name = user_info.first_name or ""
        if user_info.last_name:
            name += f" {user_info.last_name}"
        username = f" (@{user_info.username})" if user_info.username else ""
        text += f"\nИмя: {name}{username}"
    except Exception:
        pass

    await callback.message.edit_text(
        text,
        reply_markup=admin_admin_manage_kb(target_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin_revoke_admin:"))
async def admin_revoke_admin_callback(callback: CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("У вас нет прав для этого.", show_alert=True)
        return
    
    target_id = int(callback.data.split(":")[1])
    
    # Remove from set
    admin_service.SECONDARY_ADMINS.discard(target_id)

    await callback.message.edit_text(
        f"✅ Права администратора у ID {target_id} успешно отозваны.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 К списку админов", callback_data="admin_admins_list")
        ]]),
    )
    await callback.answer("Амдин удалён!")

    # Notify the user
    try:
        await callback.bot.send_message(
            chat_id=target_id,
            text="❌ <b>Ваш доступ в панель администратора был отозван главным администратором.</b>",
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"Failed to notify revoked admin {target_id}: {e}")


@router.callback_query(F.data == "admin_panel_back")
async def admin_panel_back_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if not is_admin(user_id):
        return
    await callback.message.edit_text(
        "🛠 <b>Панель администратора</b>",
        reply_markup=admin_panel_kb(is_main_admin=(user_id in ADMIN_IDS)),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_drlist")
async def admin_drivers_list_callback(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        drivers = await driver_service.get_active_drivers(session)
    
    if not drivers:
        await callback.answer("В базе нет активных водителей.", show_alert=True)
        return

    await callback.message.edit_text(
        "👥 <b>Список активных водителей:</b>\nВыберите для управления:",
        reply_markup=admin_drivers_list_kb(drivers),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin_drv:"))
async def admin_driver_view_callback(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        return
    
    driver_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        driver = await driver_service.get_driver_by_user_id(session, driver_id)
        
    if not driver:
        await callback.answer("Водитель не найден.", show_alert=True)
        return

    text = (
        f"🚘 <b>Водитель:</b> {driver.name}\n"
        f"📞 <b>Телефон:</b> {driver.phone}\n"
        f"🚗 <b>Авто:</b> {driver.car_model}\n"
        f"🔢 <b>Номер:</b> {driver.car_number}\n"
        f"📊 <b>Текущий статус:</b> {driver.status}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=admin_driver_manage_kb(driver_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin_del_drv:"))
async def admin_driver_delete_callback(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        return
    
    driver_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        success = await driver_service.deactivate_driver(session, driver_id)
        
    if success:
        await callback.message.edit_text(
            "✅ <b>Водитель заблокирован (удалён).</b>\nОн больше не сможет принимать заказы.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 К списку", callback_data="admin_drlist")
            ]]),
            parse_mode="HTML",
        )
        await callback.answer("Водитель удалён!")
        
        # Notify the banned driver
        try:
            await callback.bot.send_message(
                chat_id=driver_id,
                text="❌ <b>Ваш аккаунт водителя был деактивирован администратором.</b>",
                parse_mode="HTML",
            )
        except Exception as e:
            print(f"Could not notify banned driver {driver_id}: {e}")
# ── Admin: Add Driver FSM ──────────────────────────────────────────────────
from aiogram.fsm.context import FSMContext
from states.admin import AdminAddDriverFSM


@router.callback_query(F.data == "admin_add_drv")
async def admin_add_drv_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminAddDriverFSM.waiting_user_id)
    await callback.message.edit_text(
        "➕ <b>Добавление водителя</b>\n\n"
        "Введите <b>числовой Telegram ID</b> водителя:\n"
        "<i>(Водитель может узнать его, написав @userinfobot)</i>",
        parse_mode="HTML",
    )


@router.message(AdminAddDriverFSM.waiting_user_id)
async def admin_add_drv_id(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    if not message.text.isdigit():
        await message.answer("❌ ID должен быть числовым. Попробуйте ещё раз:")
        return
    
    user_id = int(message.text)
    
    # Check if driver already exists
    async with AsyncSessionLocal() as session:
        existing = await driver_service.get_driver_by_user_id(session, user_id)
        if existing:
            await message.answer(
                "❌ Водитель с таким ID уже зарегистрирован в базе.",
                reply_markup=admin_panel_kb(is_main_admin=(message.from_user.id in ADMIN_IDS))
            )
            await state.clear()
            return

    await state.update_data(user_id=user_id)
    await state.set_state(AdminAddDriverFSM.waiting_name)
    await message.answer("👤 Введите полное имя водителя:")


@router.message(AdminAddDriverFSM.waiting_name)
async def admin_add_drv_name(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text)
    await state.set_state(AdminAddDriverFSM.waiting_phone)
    await message.answer("📞 Введите телефон (например: +998901234567):")


@router.message(AdminAddDriverFSM.waiting_phone)
async def admin_add_drv_phone(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.update_data(phone=message.text)
    await state.set_state(AdminAddDriverFSM.waiting_car_model)
    await message.answer("🚗 Введите марку авто (например: Chevrolet Cobalt):")


@router.message(AdminAddDriverFSM.waiting_car_model)
async def admin_add_drv_car_model(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.update_data(car_model=message.text)
    await state.set_state(AdminAddDriverFSM.waiting_car_number)
    await message.answer("🔢 Введите номер авто (например: 01 A 123 BA):")


@router.message(AdminAddDriverFSM.waiting_car_number)
async def admin_add_drv_car_number(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.update_data(car_number=message.text)
    
    data = await state.get_data()
    await state.clear()
    
    async with AsyncSessionLocal() as session:
        added = await driver_service.add_driver(
            session=session,
            user_id=data["user_id"],
            name=data["name"],
            phone=data["phone"],
            car_model=data["car_model"],
            car_number=data["car_number"],
        )
        
    if added:
        await message.answer(
            f"✅ <b>Водитель успешно добавлен!</b>\n\n"
            f"👤 {data['name']}\n"
            f"🚗 {data['car_model']} ({data['car_number']})",
            reply_markup=admin_panel_kb(is_main_admin=(message.from_user.id in ADMIN_IDS)),
            parse_mode="HTML"
        )
        try:
            await message.bot.send_message(
                chat_id=data["user_id"],
                text="🎉 <b>Вы были добавлены в систему как водитель!</b>\n"
                     "Теперь вы можете принимать заказы.",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Could not notify added driver {data['user_id']}: {e}")
            await message.answer("⚠️ Водитель добавлен, но не удалось отправить ему уведомление (возможно он не запустил бота).")
    else:
        await message.answer("❌ Ошибка при добавлении (возможно, такой ID уже есть).", reply_markup=admin_panel_kb(is_main_admin=(message.from_user.id in ADMIN_IDS)))
