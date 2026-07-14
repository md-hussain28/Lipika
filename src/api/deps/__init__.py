"""
API dependency injection package.

Layout:
  common.py  — infrastructure (DB, Redis, Settings, AI)
  auth.py    — auth feature (UserDAO, RegisterService, …)

Endpoints can import either way:

  from src.api.deps import DBSession, RegisterServiceDep
  from src.api.deps.auth import RegisterServiceDep
"""

from src.api.deps.auth import RegisterServiceDep, UserDAODep
from src.api.deps.common import (
    AIClient,
    DBSession,
    RedisClient,
    RequiredAIClient,
    SettingsDep,
)

__all__ = [
    "AIClient",
    "DBSession",
    "RedisClient",
    "RegisterServiceDep",
    "RequiredAIClient",
    "SettingsDep",
    "UserDAODep",
]
