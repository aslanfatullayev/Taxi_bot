"""
Client handlers — FSM order flow.

States:
  waiting_from → waiting_to → confirm → (order created & saved to DB)
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

from db import AsyncSessionLocal
from keyboards.client_kb import (
    client_main_kb, confirm_order_kb, location_request_kb, 
    client_cancel_order_kb, client_cancel_reason_kb
)
from keyboards.driver_kb import accept_order_kb
from states.client import ClientCancelOrderFSM
from models.order import OrderStatus
from services import order_service
from states.order import OrderFSM

router = Router()

# ── General Cancellation ───────────────────────────────────────────────────
@router.message(F.text == "❌ Отмена")
async def general_cancel(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("❌ Действие отменено.", reply_markup=client_main_kb())



# ── Step 1: Client presses "Заказать такси" ────────────────────────────────
@router.message(F.text == "🚖 Заказать такси")
async def start_order(message: Message, state: FSMContext) -> None:
    async with AsyncSessionLocal() as session:
        from services.client_service import get_client_by_user_id
        client = await get_client_by_user_id(session, message.from_user.id)
    if not client:
        await message.answer(
            "⚠️ Сначала пройдите быструю регистрацию.\nОтправьте команду /start",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await state.set_state(OrderFSM.waiting_from)
    await message.answer(
        "📍 Откуда вас забрать?\n"
        "Отправьте геолокацию или напишите адрес вручную:",
        reply_markup=location_request_kb(),
    )


# ── Step 2: Receive pickup location ───────────────────────────────────────
@router.message(OrderFSM.waiting_from)
async def get_from_location(message: Message, state: FSMContext) -> None:
    if message.location:
        loc = f"{message.location.latitude}, {message.location.longitude}"
    elif message.text and message.text != "✏️ Написать адрес вручную":
        loc = message.text
    else:
        await message.answer(
            "Пожалуйста, отправьте геолокацию или просто напишите адрес текстом:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await state.update_data(from_location=loc)
    await state.set_state(OrderFSM.waiting_to)
    await message.answer(
        "🏁 Куда едем?\nОтправьте геолокацию или напишите адрес вручную:",
        reply_markup=location_request_kb(),
    )


# ── Step 3: Receive destination ────────────────────────────────────────────
@router.message(OrderFSM.waiting_to)
async def get_to_location(message: Message, state: FSMContext) -> None:
    if message.location:
        loc = f"{message.location.latitude}, {message.location.longitude}"
    elif message.text and message.text != "✏️ Написать адрес вручную":
        loc = message.text
    else:
        await message.answer(
            "Пожалуйста, отправьте геолокацию или просто напишите адрес текстом:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await state.update_data(to_location=loc)
    data = await state.get_data()
    await state.set_state(OrderFSM.confirm)
    
    # Check if they are coordinates to format them slightly differently if wanted, 
    # but for now we just show string "lat, lon" or "Address name"
    await message.answer(
        f"📋 Подтвердите заказ:\n\n"
        f"📍 Откуда: {data['from_location']}\n"
        f"🏁 Куда: {data['to_location']}\n\n"
        f"Всё верно?",
        reply_markup=confirm_order_kb(),
    )


# ── Step 4: Client confirm options handled below and by general cancel ─────


# ── Step 4b: Client confirms — order saved to DB & sent to random driver ───
@router.message(OrderFSM.confirm, F.text == "✅ Подтвердить")
async def confirm_order(message: Message, state: FSMContext) -> None:
    import random
    from services import driver_service

    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        from services.client_service import get_client_by_user_id
        client = await get_client_by_user_id(session, message.from_user.id)
        client_name = client.name if client else "Неизвестно"
        client_phone = client.phone if client else "Не указан"

        order = await order_service.create_order(
            session=session,
            user_id=message.from_user.id,
            from_location=data["from_location"],
            to_location=data["to_location"],
        )
        order_id = order.id
        from_loc = order.from_location
        to_loc = order.to_location

        # Only idle drivers can receive new orders
        driver_ids = await driver_service.get_available_driver_ids(session)

    if not driver_ids:
        await message.answer(
            "⚠️ К сожалению, сейчас нет доступных водителей. Попробуйте позже.",
            reply_markup=client_main_kb(),
        )
        return

    await message.answer(
        "✅ Заказ принят! Ищем водителя...",
        reply_markup=client_main_kb(),
    )
    await message.answer(
        f"Ваш заказ #{order_id} находится в поиске водителя.",
        reply_markup=client_cancel_order_kb(order_id),
    )

    driver_text = (
        f"🚖 Новый заказ!\n\n"
        f"🆔 Заказ #{order_id}\n"
        f"👤 Клиент: {client_name}\n"
        f"📞 Телефон: {client_phone}\n"
        f"📍 Откуда: {from_loc}\n"
        f"🏁 Куда: {to_loc}\n\n"
        f"Нажмите «Принять», чтобы взять заказ."
    )

    import logging
    import random

    # Shuffle and try each driver until one successfully receives the message.
    # This handles cases where a driver blocked the bot or has a fake/outdated ID.
    random.shuffle(driver_ids)
    sent = False
    for driver_id in driver_ids:
        try:
            await message.bot.send_message(
                chat_id=driver_id,
                text=driver_text,
                reply_markup=accept_order_kb(order_id),
            )
            sent = True
            logging.info(f"Order #{order_id} sent to driver {driver_id}")
            break
        except Exception as e:
            logging.warning(f"Could not send order to driver {driver_id}: {e}")
            continue

    if not sent:
        await message.answer(
            "⚠️ Не удалось найти доступного водителя. Попробуйте позже."
        )


# ── Client Cancels Active Order ────────────────────────────────────────────

@router.callback_query(F.data.startswith("client_cancel_order:"))
async def on_client_cancel_order(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.split(":")[1])
    await state.set_state(ClientCancelOrderFSM.waiting_reason)
    await state.update_data(cancel_order_id=order_id)
    await callback.message.edit_text(
        "Напишите, пожалуйста, причину отмены заказа:",
        reply_markup=client_cancel_reason_kb()
    )


@router.callback_query(F.data == "abort_client_cancel")
async def on_abort_client_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    
    # Ideally we'd restore the cancel button, but for simplicity we can just say resumed.
    await callback.message.edit_text("Отмена прервана. Ожидайте водителя.")


@router.message(ClientCancelOrderFSM.waiting_reason)
async def process_cancel_reason(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("cancel_order_id")
    reason = message.text

    async with AsyncSessionLocal() as session:
        order = await order_service.get_order(session, order_id)
        if not order:
            await state.clear()
            await message.answer("Ошибка: Заказ не найден.")
            return

        if order.status == OrderStatus.CANCELLED:
            await state.clear()
            await message.answer("Заказ уже был отменен.")
            return
            
        if order.status == OrderStatus.COMPLETED:
            await state.clear()
            await message.answer("Заказ уже завершен.")
            return

        # Cancel the order
        await order_service.update_order_status(session, order_id, OrderStatus.CANCELLED)

        # Notify assigned driver if there is one
        if order.driver_id:
            from services.driver_service import get_driver_by_user_id, update_driver_status
            from models.driver import DriverStatus
            driver = await get_driver_by_user_id(session, order.driver_id)
            if driver:
                await update_driver_status(session, driver.id, DriverStatus.IDLE)
                try:
                    await message.bot.send_message(
                        chat_id=driver.user_id,
                        text=(
                            f"⚠️ <b>Клиент отменил заказ #{order_id}!</b>\n\n"
                            f"<b>Причина:</b> {reason}\n\n"
                            f"<i>Ваш статус изменен на 'Свободен'.</i>"
                        ),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"Failed to notify driver {driver.user_id}: {e}")

    await state.clear()
    await message.answer(
        "✅ Ваш заказ успешно отменен.",
        reply_markup=client_main_kb()
    )
