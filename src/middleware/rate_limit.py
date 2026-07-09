"""
Rate limiting setup using SlowAPI.

Protects expensive endpoints (especially AI calls) from abuse by capping
how many requests a single IP address can make per minute.

Uses Redis as the shared storage backend when REDIS_URL is set (multi-server
deployments). Falls back to in-memory storage for local development.
"""

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from src.core.config import Settings

# Placeholder limiter so @limiter.limit decorators can bind at import time.
# setup_rate_limiting() always rebuilds this from the app's settings.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
    storage_uri="memory://",
)


def setup_rate_limiting(app: FastAPI, settings: Settings) -> Limiter:
    """
    Attach SlowAPI middleware and exception handler to the FastAPI app.

    The limiter is rebuilt from `settings` on every app creation so it stays
    in sync with app.state.settings (including test overrides).
    """
    global limiter
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
        storage_uri=settings.REDIS_URL if settings.redis_enabled else "memory://",
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    return limiter
