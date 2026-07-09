"""
Application lifespan — startup and shutdown hooks.

FastAPI runs code BEFORE `yield` when the server starts (opening connections)
and AFTER `yield` when the server stops (closing connections cleanly).
Without this, database pools and HTTP clients leak memory on every deploy.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.config import Settings
from src.db import models  # noqa: F401 — registers models with Base.metadata
from src.db.base import Base
from src.db.session import create_engine, create_session_factory
from src.services.ai_client import create_ai_client
from src.services.redis_client import close_redis_client, create_redis_client

logger = structlog.get_logger(__name__)


async def _create_tables(engine: AsyncEngine) -> None:
    """
    Create all tables that don't exist yet.

    Fine for development and small projects. In production you should switch
    to Alembic migrations for safe, versioned schema changes.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async context manager wired into FastAPI via lifespan=lifespan.

    Resources are stored on app.state so route handlers access them via:
        request.app.state.db_session_factory
        request.app.state.redis
        request.app.state.ai_client
    """
    settings: Settings = app.state.settings

    logger.info(
        "application_starting",
        project=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
    )

    # ── STARTUP: open long-lived resources ──────────────────────────────

    # 1. Database engine + session factory
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    await _create_tables(engine)

    app.state.db_engine = engine
    app.state.db_session_factory = session_factory

    logger.info("database_connected", url=settings.DATABASE_URL.split("@")[-1])

    # 2. Redis (optional — skipped when REDIS_URL is empty)
    redis = await create_redis_client(settings)
    app.state.redis = redis
    logger.info("redis_status", enabled=redis is not None)

    # 3. OpenAI client (optional — skipped when OPENAI_API_KEY is empty)
    ai_client = create_ai_client(settings)
    app.state.ai_client = ai_client
    logger.info("ai_client_status", enabled=ai_client is not None)

    logger.info("resources_initialized")

    yield

    # ── SHUTDOWN: close resources in reverse order ──────────────────────
    logger.info("application_shutting_down")

    await close_redis_client(app.state.redis)
    await app.state.db_engine.dispose()

    logger.info("resources_cleaned_up")
