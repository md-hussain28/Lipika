"""
Central model registry.

Every ORM model must be imported here. This is the single place that wires
SQLAlchemy metadata, relationship resolution, and Alembic autogenerate.

Individual model files must NOT import each other at runtime — use string
names in relationship() and TYPE_CHECKING imports from this package only:

    if TYPE_CHECKING:
        from src.db.models import OtherModel

Application code must import models from here, never from submodules:

    from src.db.models import Note

Loaded at startup by:
  - src.core.lifespan (app)
  - alembic/env.py (migrations)
"""

from src.db.models.note import Note
from src.db.models.session import Session
from src.db.models.user import User

__all__ = ["Note", "Session", "User"]
