from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.client import Client


async def get_client_by_user_id(session: AsyncSession, user_id: int) -> Client | None:
    """Fetch a client by their Telegram user ID."""
    result = await session.execute(select(Client).where(Client.user_id == user_id))
    return result.scalar_one_or_none()


async def add_client(
    session: AsyncSession,
    user_id: int,
    name: str,
    phone: str,
) -> bool:
    """Add a new client to the database. Returns True if successfully added."""
    existing = await get_client_by_user_id(session, user_id)
    if existing:
        return False
        
    client = Client(
        user_id=user_id,
        name=name,
        phone=phone,
    )
    session.add(client)
    await session.commit()
    return True
