from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import UUID as UUID_TYPE

from sqlalchemy import UUID, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid4, uuid7

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.db.models import User


def _default_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=7)


class Session(Base, TimestampMixin):
    __tablename__ = "sessions"

    id: Mapped[UUID_TYPE] = mapped_column(UUID, primary_key=True, default=uuid7)
    user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[UUID_TYPE] = mapped_column(
        UUID, nullable=False, default=uuid4, unique=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_default_expires_at, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="sessions")
