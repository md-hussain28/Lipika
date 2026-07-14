"""
Async database engine and session factory.

SQLAlchemy 2.0 async pattern:
  - One engine per process (connection pool lives here)
  - One session per request (opened in get_db, closed after the response)
  - Never share sessions across concurrent requests
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """
    Build the async SQLAlchemy engine with a connection pool.

    Creating an engine does NOT open a connection — call verify_connection()
    at startup to fail fast when the database is unreachable.

    SQLite (dev default):  sqlite+aiosqlite:///./lipika.db
    PostgreSQL (prod):   postgresql+asyncpg://user:pass@host:5432/lipika
    """
    connect_args: dict = {}
    if settings.DATABASE_URL.startswith("sqlite"):
        # Required for SQLite when using the same file across async tasks.
        connect_args["check_same_thread"] = False

    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,  # verify connections before use (handles stale pool conns)
        connect_args=connect_args,
    )


async def verify_connection(engine: AsyncEngine) -> None:
    """Open a real connection and run SELECT 1 — raises if the database is down."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Session factory bound to the engine — call it to get a new AsyncSession."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,  # objects stay usable after commit (handy for returning from routes)
        autoflush=False,
        autocommit=False,
    )


async def get_db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """
    Yield one database session per request, always closing it afterward.

    Used internally by the FastAPI dependency in api/deps.py.
    """
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
