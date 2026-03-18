"""
Order service — async repository layer.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.order import Order, OrderStatus


async def create_order(
    session: AsyncSession,
    user_id: int,
    from_location: str,
    to_location: str,
) -> Order:
    """Insert a new pending order and return it."""
    order = Order(
        user_id=user_id,
        from_location=from_location,
        to_location=to_location,
        status=OrderStatus.PENDING,
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    """Fetch an order by primary key."""
    return await session.get(Order, order_id)


async def accept_order(
    session: AsyncSession,
    order_id: int,
    driver_id: int,
) -> Order | None:
    """
    Assign a driver to a pending order.
    Returns updated Order, or None if already taken / not found.
    """
    order = await session.get(Order, order_id)
    if order is None or order.status != OrderStatus.PENDING:
        return None

    order.status = OrderStatus.ACCEPTED
    order.driver_id = driver_id
    await session.commit()
    await session.refresh(order)
    return order


async def complete_order(
    session: AsyncSession,
    order_id: int,
) -> Order | None:
    """
    Mark an accepted order as completed.
    Returns updated Order, or None if not found / not in accepted state.
    """
    order = await session.get(Order, order_id)
    if order is None or order.status != OrderStatus.ACCEPTED:
        return None

    order.status = OrderStatus.COMPLETED
    await session.commit()
    await session.refresh(order)
    return order


async def get_all_orders(session: AsyncSession) -> list[Order]:
    """Return all orders (useful for admin/debug)."""
    result = await session.execute(select(Order))
    return list(result.scalars().all())
