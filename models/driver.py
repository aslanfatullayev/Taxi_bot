from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class DriverStatus:
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"


class Driver(Base):
    __tablename__ = "drivers"
    __table_args__ = (UniqueConstraint("user_id", name="uq_driver_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    car_model: Mapped[str] = mapped_column(String, nullable=False)
    car_number: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default=DriverStatus.IDLE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
