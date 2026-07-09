"""
SQLAlchemy declarative base — the foundation for all ORM models.

Every database table is a Python class that inherits from Base.
Alembic migrations (when you add them) also import this Base to autogenerate schema diffs.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared metadata registry for all ORM models in this application."""

    pass


class TimestampMixin:
    """Reusable created_at / updated_at columns for domain models."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
