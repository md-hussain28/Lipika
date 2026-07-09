"""
Global exception handlers — uniform JSON errors for every failure mode.

Without these, FastAPI returns inconsistent shapes (and unhandled exceptions
leak raw Python tracebacks to clients). Every error response follows the same
schema so frontends can display messages reliably.
"""

from typing import Any, cast

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ExceptionHandler

logger = structlog.get_logger(__name__)


def _error_body(
    *, code: int, message: str, details: list[Any] | dict[str, Any] | None = None
) -> dict[str, Any]:
    """Single error envelope used by every handler below."""
    body: dict = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handles HTTPException (404, 403, etc.) raised explicitly in route code.

    Example: raise HTTPException(status_code=404, detail="User not found")
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(code=exc.status_code, message=str(exc.detail)),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handles Pydantic validation errors (bad JSON, missing fields, wrong types).

    Returns field-level details so the frontend can highlight invalid inputs.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_body(
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Request validation failed",
            details=list(exc.errors()),
        ),
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Catch-all for unexpected crashes.

    Logs the full traceback server-side but returns a generic message to the
    client — never expose internal stack traces publicly.
    """
    logger.exception(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred. Please try again later.",
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all handlers to the FastAPI instance (called once in the factory)."""
    app.add_exception_handler(
        StarletteHTTPException, cast(ExceptionHandler, http_exception_handler)
    )
    app.add_exception_handler(
        RequestValidationError, cast(ExceptionHandler, validation_exception_handler)
    )
    app.add_exception_handler(Exception, unhandled_exception_handler)
