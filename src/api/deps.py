"""
FastAPI dependency injection — reusable Depends() callables for routes.

Instead of reaching into request.app.state manually in every endpoint,
declare what you need as a function parameter:

    async def my_route(db: DBSession, redis: RedisClient): ...
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from openai import AsyncOpenAI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.config import Settings
from src.db.session import get_db_session


def get_app_settings(request: Request) -> Settings:
    """Return settings for the app handling this request."""
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]


def _get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.app.state.db_session_factory


async def get_db(
    session_factory: Annotated[
        async_sessionmaker[AsyncSession], Depends(_get_session_factory)
    ],
) -> AsyncGenerator[AsyncSession, None]:
    """
    Inject a database session into any route.

    Commits on success, rolls back on exception, always closes the session.
    """
    async for session in get_db_session(session_factory):
        yield session


DBSession = Annotated[AsyncSession, Depends(get_db)]


def get_redis(request: Request) -> Redis | None:
    """Return the shared Redis client, or None if Redis is not configured."""
    return request.app.state.redis


RedisClient = Annotated[Redis | None, Depends(get_redis)]


def get_ai_client(request: Request) -> AsyncOpenAI | None:
    """Return the shared OpenAI client, or None if no API key is configured."""
    return request.app.state.ai_client


AIClient = Annotated[AsyncOpenAI | None, Depends(get_ai_client)]


def require_ai_client(
    ai_client: AIClient,
) -> AsyncOpenAI:
    """
    Like get_ai_client but raises 503 when AI is not configured.

    Use this on routes that cannot function without OpenAI.
    """
    if ai_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured. Set OPENAI_API_KEY in .env",
        )
    return ai_client


RequiredAIClient = Annotated[AsyncOpenAI, Depends(require_ai_client)]
