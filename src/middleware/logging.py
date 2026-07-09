"""
Structured request/response logging middleware.

For every HTTP call this middleware:
  1. Generates a unique request_id (UUID)
  2. Binds it to structlog's context so ALL logs during that request include it
  3. Logs method, path, status code, and duration when the response completes

In production you can grep logs by request_id to trace a single user's journey.
"""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that wraps every request with structured log entries."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Unique ID for this request — also returned in X-Request-ID header.
        request_id = str(uuid.uuid4())

        # Bind request_id to structlog contextvars so nested log calls inherit it.
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()

        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        # Echo request_id back so frontend/support can reference it in bug reports.
        response.headers["X-Request-ID"] = request_id
        return response
