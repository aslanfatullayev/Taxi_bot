"""
Driver handlers:
  - accept_order   → status = busy, send driver info to client (YandexGo style)
  - complete_trip  → order status = completed, driver status = idle
  - go_offline     → driver status = offline
"""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from db import AsyncSessionLocal
from keyboards.driver_kb import driver_active_kb
from models.driver import DriverStatus
from services import driver_service, order_service

router = Router()


# ── Accept order ───────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("accept_order:"))
async def accept_order_callback(callback: CallbackQuery) -> None:
    order_id = int(callback.data.split(":")[1])
    driver_user_id = callback.from_user.id

    async with AsyncSessionLocal() as session:
        order = await order_service.accept_order(session, order_id, driver_user_id)
        if order is None:
            await callback.answer("⚠️ Заказ уже принят другим водителем.", show_alert=True)
            return

        driver = await driver_service.get_driver_by_user_id(session, driver_user_id)
        await driver_service.set_driver_status(session, driver_user_id, DriverStatus.BUSY)

        client_id = order.user_id
        from_loc = order.from_location
        to_loc = order.to_location

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"✅ Вы приняли заказ #{order_id}!\n"
        f"📍 Откуда: {from_loc}\n"
        f"🏁 Куда: {to_loc}\n\n"
        f"Удачной поездки! 🚗",
        reply_markup=driver_active_kb(order_id),
    )
    await callback.answer()

    # Send driver info to client (YandexGo style)
    try:
        driver_info = (
            f"🎉 Водитель найден!\n\n"
            f"👤 Имя: {driver.name}\n"
            f"📞 Телефон: {driver.phone}\n"
            f"🚗 Авто: {driver.car_model}\n"
            f"🔢 Номер авто: {driver.car_number}\n\n"
            f"Водитель уже едет к вам!"
        )
        await callback.bot.send_message(chat_id=client_id, text=driver_info)
    except Exception as e:
        logging.warning(f"Could not notify client {client_id}: {e}")


# ── Complete trip ──────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("complete_trip:"))
async def complete_trip_callback(callback: CallbackQuery) -> None:
    order_id = int(callback.data.split(":")[1])
    driver_user_id = callback.from_user.id

    async with AsyncSessionLocal() as session:
        order = await order_service.complete_order(session, order_id)
        if order is None:
            await callback.answer("⚠️ Заказ не найден или уже завершён.", show_alert=True)
            return

        await driver_service.set_driver_status(session, driver_user_id, DriverStatus.IDLE)
        client_id = order.user_id

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"✅ Поездка #{order_id} завершена!\n"
        f"Вы снова свободны и готовы к новым заказам. 👍"
    )
    await callback.answer()

    try:
        await callback.bot.send_message(
            chat_id=client_id,
            text="🏁 Ваша поездка завершена!\nСпасибо, что воспользовались нашим сервисом. 🙏",
        )
    except Exception as e:
        logging.warning(f"Could not notify client {client_id}: {e}")


# ── Go offline ─────────────────────────────────────────────────────────────
@router.callback_query(F.data == "go_offline")
async def go_offline_callback(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        await driver_service.set_driver_status(
            session, callback.from_user.id, DriverStatus.OFFLINE
        )

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "📴 Вы завершили работу. До свидания!\n"
        "Чтобы снова принимать заказы — нажмите 🚗 Хочу стать водителем."
    )
    await callback.answer()
