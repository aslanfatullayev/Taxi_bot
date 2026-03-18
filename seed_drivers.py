"""
Seed script — добавляет реальных водителей в базу.

Запуск:
    python seed_drivers.py

⚠️  Замените YOUR_TELEGRAM_ID на реальный Telegram user_id.
    Узнать свой ID можно через @userinfobot в Telegram.
"""

import asyncio

from db import init_db, AsyncSessionLocal
from models.driver import DriverStatus
from services.driver_service import add_driver

# ── Список реальных водителей ──────────────────────────────────────────────
# Заполните user_id реальными Telegram ID водителей.
DRIVERS = [
    {"user_id": 1517967852, "name": "Азиз",    "car_model": "KIA K5"},
    # {"user_id": 000000002, "name": "Дилшод",  "car_model": "KIA K5"},
    # {"user_id": 000000003, "name": "Бекзод",  "car_model": "KIA K5"},
    # Раскомментируйте и заполните по мере появления водителей
]


async def seed() -> None:
    await init_db()

    async with AsyncSessionLocal() as session:
        for driver in DRIVERS:
            added = await add_driver(
                session=session,
                user_id=driver["user_id"],
                name=driver["name"],
                car_model=driver["car_model"],
            )
            status = "✅ добавлен" if added else "⚠️  уже есть"
            print(f"{status} — {driver['name']} (ID: {driver['user_id']}, {driver['car_model']})")

    print("\nГотово!")


if __name__ == "__main__":
    asyncio.run(seed())
