"""
Common handlers: /start command, language selection, and client registration.
"""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from config import DRIVER_IDS
from keyboards.client_kb import client_main_kb, language_select_kb
from db import AsyncSessionLocal
from services import client_service
from states.client import LanguageSelectFSM, ClientRegistrationFSM
from locales import t

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    await state.clear()

    if user_id in DRIVER_IDS:
        await message.answer(t("driver_greeting"))
        return

    # Check if client exists and has chosen a language already
    async with AsyncSessionLocal() as session:
        client = await client_service.get_client_by_user_id(session, user_id)

    if client:
        lang = client.lang
        await message.answer(
            t("registered_greeting", lang).format(name=client.name),
            reply_markup=client_main_kb(lang),
        )
    else:
        # Ask language first
        await state.set_state(LanguageSelectFSM.waiting_language)
        await message.answer(
            t("choose_language"),
            reply_markup=language_select_kb(),
        )


@router.message(LanguageSelectFSM.waiting_language)
async def select_language(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    if "O'zbek" in text or "uzbek" in text.lower():
        lang = "uz"
    else:
        lang = "ru"

    await state.update_data(lang=lang)
    await state.set_state(ClientRegistrationFSM.waiting_name)
    await message.answer(
        t("welcome_new", lang),
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(ClientRegistrationFSM.waiting_name)
async def process_client_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await state.update_data(name=message.text)
    await state.set_state(ClientRegistrationFSM.waiting_phone)
    await message.answer(t("ask_phone", lang))


@router.message(ClientRegistrationFSM.waiting_phone)
async def process_client_phone(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    name = data["name"]
    lang = data.get("lang", "ru")
    phone = message.text

    async with AsyncSessionLocal() as session:
        await client_service.add_client(session, message.from_user.id, name, phone, lang)

    await state.clear()
    await message.answer(
        t("registration_done", lang).format(name=name),
        reply_markup=client_main_kb(lang),
    )
