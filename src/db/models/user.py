from typing import TYPE_CHECKING
from uuid import UUID as UUID_TYPE

from sqlalchemy import UUID, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.db.models import Session


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[UUID_TYPE] = mapped_column(UUID, primary_key=True, default=uuid7)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
