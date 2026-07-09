"""
Redis client factory — optional caching and shared rate-limit storage.

Redis is optional: if REDIS_URL is empty the app starts without it.
Routes that need caching should check `request.app.state.redis` for None.
"""

from redis.asyncio import Redis

from src.core.config import Settings


async def create_redis_client(settings: Settings) -> Redis | None:
    """
    Connect to Redis if REDIS_URL is configured.

    Returns None when Redis is disabled — callers must handle that gracefully.
    """
    if not settings.REDIS_URL:
        return None

    client = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    # Verify the connection is alive before storing on app.state.
    await client.ping()
    return client


async def close_redis_client(client: Redis | None) -> None:
    """Gracefully close the Redis connection pool on shutdown."""
    if client is not None:
        await client.aclose()
