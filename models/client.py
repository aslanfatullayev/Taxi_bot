from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class Client(Base):
    """Database model for registered clients."""
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    lang: Mapped[str] = mapped_column(String(5), nullable=False, default="ru")

