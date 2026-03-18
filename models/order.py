from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class OrderStatus:
    PENDING = "pending"
    ACCEPTED = "accepted"
    COMPLETED = "completed"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    from_location: Mapped[str] = mapped_column(String, nullable=False)
    to_location: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default=OrderStatus.PENDING, nullable=False)
    driver_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
