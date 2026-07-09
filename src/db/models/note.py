"""
Example Note model — demonstrates the full DB stack end-to-end.

Replace or extend this as you build real domain models (users, posts, etc.).
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class Note(Base, TimestampMixin):
    """A simple text note stored in the database."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
