"""
Driver service — async repository layer.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.driver import Driver, DriverStatus


async def add_driver(
    session: AsyncSession,
    user_id: int,
    name: str,
    phone: str,
    car_model: str,
    car_number: str,
) -> bool:
    """
    Register a new driver with status=idle.
    Returns True if added, False if already exists.
    """
    driver = Driver(
        user_id=user_id,
        name=name,
        phone=phone,
        car_model=car_model,
        car_number=car_number,
        status=DriverStatus.IDLE,
    )
    session.add(driver)
    try:
        await session.commit()
        return True
    except IntegrityError:
        await session.rollback()
        return False


async def get_driver_by_user_id(session: AsyncSession, user_id: int) -> Driver | None:
    """Fetch a driver by their Telegram user_id."""
    result = await session.execute(
        select(Driver).where(Driver.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_available_drivers(session: AsyncSession) -> list[Driver]:
    """Return all drivers with status=idle."""
    result = await session.execute(
        select(Driver).where(
            Driver.status == DriverStatus.IDLE,
            Driver.is_active == True,  # noqa: E712
        )
    )
    return list(result.scalars().all())


async def get_available_driver_ids(session: AsyncSession) -> list[int]:
    """Return user_ids of available (idle) drivers."""
    drivers = await get_available_drivers(session)
    return [d.user_id for d in drivers]


async def set_driver_status(
    session: AsyncSession,
    user_id: int,
    status: str,
) -> bool:
    """Update a driver's status. Returns True if updated."""
    driver = await get_driver_by_user_id(session, user_id)
    if driver is None:
        return False
    driver.status = status
    await session.commit()
    return True


async def get_all_drivers(session: AsyncSession) -> list[Driver]:
    """Return all drivers regardless of status."""
    result = await session.execute(select(Driver))
    return list(result.scalars().all())
