"""
SQLAlchemy declarative base — the foundation for all ORM models.

Every database table is a Python class that inherits from Base.
Alembic migrations (when you add them) also import this Base to autogenerate schema diffs.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared metadata registry for all ORM models in this application."""

    pass
