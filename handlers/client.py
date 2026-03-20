"""
Client handlers — FSM order flow (bilingual).
"""

import logging
import random

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

from db import AsyncSessionLocal
from keyboards.client_kb import (
    client_main_kb, confirm_order_kb, location_request_kb,
    client_cancel_order_kb,
)
from keyboards.driver_kb import accept_order_kb
from locales import t
from models.order import OrderStatus
from services import order_service
from states.client import ClientCancelOrderFSM
from states.order import OrderFSM

router = Router()


async def _get_lang(user_id: int) -> str:
    """Helper: fetch client language from DB, default 'ru'."""
    from services.client_service import get_client_by_user_id
    async with AsyncSessionLocal() as session:
        client = await get_client_by_user_id(session, user_id)
    return client.lang if client else "ru"


# ── General Cancellation ───────────────────────────────────────────────────
@router.message(F.text.in_({"❌ Отмена", "❌ Bekor qilish"}))
async def general_cancel(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    lang = await _get_lang(message.from_user.id)
    await state.clear()
    await message.answer(t("action_cancelled", lang), reply_markup=client_main_kb(lang))


# ── Step 1: Order taxi ─────────────────────────────────────────────────────
@router.message(F.text.in_({"🚖 Заказать такси", "🚖 Taksi chaqirish"}))
async def start_order(message: Message, state: FSMContext) -> None:
    lang = await _get_lang(message.from_user.id)

    current_state = await state.get_state()
    if current_state is not None:
        await message.answer(t("state_guard", lang))
        return

    async with AsyncSessionLocal() as session:
        from services.client_service import get_client_by_user_id
        client = await get_client_by_user_id(session, message.from_user.id)
    if not client:
        await message.answer(t("not_registered_order", lang), reply_markup=ReplyKeyboardRemove())
        return

    await state.set_state(OrderFSM.waiting_from)
    await message.answer(t("ask_from_location", lang), reply_markup=location_request_kb(lang))


# ── Step 2: Pickup location ────────────────────────────────────────────────
@router.message(OrderFSM.waiting_from)
async def get_from_location(message: Message, state: FSMContext) -> None:
    lang = await _get_lang(message.from_user.id)
    type_addr = t("btn_type_address", lang)

    if message.location:
        loc = f"{message.location.latitude}, {message.location.longitude}"
    elif message.text and message.text != type_addr:
        loc = message.text
    else:
        await message.answer(t("ask_location_again", lang), reply_markup=ReplyKeyboardRemove())
        return

    await state.update_data(from_location=loc)
    await state.set_state(OrderFSM.waiting_to)
    await message.answer(t("ask_to_location", lang), reply_markup=location_request_kb(lang))


# ── Step 3: Destination ────────────────────────────────────────────────────
@router.message(OrderFSM.waiting_to)
async def get_to_location(message: Message, state: FSMContext) -> None:
    lang = await _get_lang(message.from_user.id)
    type_addr = t("btn_type_address", lang)

    if message.location:
        loc = f"{message.location.latitude}, {message.location.longitude}"
    elif message.text and message.text != type_addr:
        loc = message.text
    else:
        await message.answer(t("ask_location_again", lang), reply_markup=ReplyKeyboardRemove())
        return

    await state.update_data(to_location=loc)
    data = await state.get_data()
    await state.set_state(OrderFSM.confirm)
    await message.answer(
        t("order_confirm_text", lang).format(
            from_loc=data["from_location"], to_loc=loc
        ),
        reply_markup=confirm_order_kb(lang),
    )


# ── Step 4b: Confirm order ─────────────────────────────────────────────────
@router.message(OrderFSM.confirm, F.text.in_({"✅ Подтвердить", "✅ Tasdiqlash"}))
async def confirm_order(message: Message, state: FSMContext) -> None:
    from services import driver_service

    lang = await _get_lang(message.from_user.id)
    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        from services.client_service import get_client_by_user_id
        client = await get_client_by_user_id(session, message.from_user.id)
        client_name = client.name if client else "—"
        client_phone = client.phone if client else "—"

        order = await order_service.create_order(
            session=session,
            user_id=message.from_user.id,
            from_location=data["from_location"],
            to_location=data["to_location"],
        )
        order_id = order.id
        from_loc = order.from_location
        to_loc = order.to_location
        driver_ids = await driver_service.get_available_driver_ids(session)

    if not driver_ids:
        await message.answer(t("no_drivers", lang), reply_markup=client_main_kb(lang))
        return

    await message.answer(t("order_accepted", lang), reply_markup=client_main_kb(lang))
    await message.answer(
        t("order_searching", lang).format(order_id=order_id),
        reply_markup=client_cancel_order_kb(order_id, lang),
    )

    driver_text = t("new_order_for_driver", "ru").format(
        order_id=order_id,
        client_name=client_name,
        client_phone=client_phone,
        from_loc=from_loc,
        to_loc=to_loc,
    )

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

    if not sent:
        await message.answer(t("no_driver_found", lang))


# ── Client cancels active order ────────────────────────────────────────────
@router.callback_query(F.data.startswith("client_cancel_order:"))
async def on_client_cancel_order(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.split(":")[1])
    lang = await _get_lang(callback.from_user.id)
    await state.set_state(ClientCancelOrderFSM.waiting_reason)
    await state.update_data(cancel_order_id=order_id)
    await callback.message.edit_text(t("ask_cancel_reason", lang))


@router.message(ClientCancelOrderFSM.waiting_reason)
async def process_cancel_reason(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("cancel_order_id")
    reason = message.text

    lang = await _get_lang(message.from_user.id)
    await state.clear()

    if not order_id:
        await message.answer(t("order_not_found", lang), reply_markup=client_main_kb(lang))
        return

    async with AsyncSessionLocal() as session:
        order = await order_service.get_order(session, order_id)

        if not order:
            await message.answer(t("order_not_found", lang), reply_markup=client_main_kb(lang))
            return
        if order.status == OrderStatus.CANCELLED:
            await message.answer(t("order_already_cancel", lang), reply_markup=client_main_kb(lang))
            return
        if order.status == OrderStatus.COMPLETED:
            await message.answer(t("order_already_done", lang), reply_markup=client_main_kb(lang))
            return

        order.status = OrderStatus.CANCELLED
        await session.commit()

        if order.driver_id:
            from services import driver_service as drv_svc
            from models.driver import DriverStatus
            await drv_svc.set_driver_status(session, order.driver_id, DriverStatus.IDLE)
            try:
                await message.bot.send_message(
                    chat_id=order.driver_id,
                    text=t("client_cancelled_order", "ru").format(
                        order_id=order_id, reason=reason
                    ),
                    parse_mode="HTML",
                )
            except Exception as e:
                print(f"Failed to notify driver {order.driver_id}: {e}")

    await message.answer(t("order_cancelled_ok", lang), reply_markup=client_main_kb(lang))
