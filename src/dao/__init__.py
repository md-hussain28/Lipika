"""Data access layer — one module per aggregate root."""

from src.dao.user import UserDAO

__all__ = ["UserDAO"]
