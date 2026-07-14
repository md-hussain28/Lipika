"""User data access — all SQL for the users table lives here."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user import User


class UserDAO:
    """Persistence operations for User records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """Return the user with the given email, or None if not found."""
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create(
        self, *, username: str, email: str, password_hash: str
    ) -> User:
        """Insert a new user and return the persisted row."""
        user = User(
            username=username,
            email=email,
            password=password_hash,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user
