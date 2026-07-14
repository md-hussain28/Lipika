"""
Auth-feature dependencies — wire UserDAO and auth services for routes.

Built on top of common.DBSession so the same request session is shared.
"""

from typing import Annotated

from fastapi import Depends

from src.api.deps.common import DBSession
from src.dao.user import UserDAO
from src.services.auth.register import RegisterService


async def get_user_dao(db: DBSession) -> UserDAO:
    """Inject a UserDAO bound to the current request session."""
    return UserDAO(db)


UserDAODep = Annotated[UserDAO, Depends(get_user_dao)]


async def get_register_service(user_dao: UserDAODep) -> RegisterService:
    """Inject the registration service."""
    return RegisterService(user_dao)


RegisterServiceDep = Annotated[RegisterService, Depends(get_register_service)]
