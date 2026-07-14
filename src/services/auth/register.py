"""User registration business logic."""

from src.dao.user import UserDAO
from src.db.models.user import User
from src.schemas.auth import UserRegisterRequest
from src.services.auth.exceptions import EmailAlreadyRegisteredError
from src.utils.security import hash_password


class RegisterService:
    """Orchestrates user registration — validation, hashing, persistence."""

    def __init__(self, user_dao: UserDAO) -> None:
        self._user_dao = user_dao

    async def register(self, data: UserRegisterRequest) -> User:
        """
        Create a new user account.

        Raises:
            EmailAlreadyRegisteredError: if the email is already taken.
        """
        existing = await self._user_dao.get_by_email(data.email)
        if existing is not None:
            raise EmailAlreadyRegisteredError(data.email)

        password_hash = hash_password(data.password)
        username = self._derive_username(data.email)

        return await self._user_dao.create(
            username=username,
            email=data.email,
            password_hash=password_hash,
        )

    @staticmethod
    def _derive_username(email: str) -> str:
        """Use the local part of the email as the default username."""
        return email.split("@", maxsplit=1)[0]
