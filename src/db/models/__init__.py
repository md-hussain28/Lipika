"""
Import all models here so Base.metadata knows about every table.

When adding a new model file, import it in this __init__.py — otherwise
create_all() and Alembic won't see the table.
"""

from src.db.models.note import Note

__all__ = ["Note"]
