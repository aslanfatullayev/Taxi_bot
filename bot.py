"""
Bot entry point.

Registers all routers and starts polling.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from db import init_db
from handlers import common, client, client_menu, driver, driver_registration, admin

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # Create DB tables on startup
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(common.router)
    dp.include_router(client_menu.router)   # profile, help, driver-section
    dp.include_router(client.router)
    dp.include_router(driver.router)
    dp.include_router(driver_registration.router)
    dp.include_router(admin.router)


    logging.info("Bot is starting...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
