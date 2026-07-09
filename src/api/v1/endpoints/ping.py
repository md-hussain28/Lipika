"""
Version 1 API endpoints.

Each feature area gets its own router file (users.py, items.py, etc.)
and they are all bundled into api_router in api/router.py.
"""

from fastapi import APIRouter

from src.api.deps import SettingsDep

router = APIRouter()


@router.get("/ping", tags=["Utility"])
async def ping(settings: SettingsDep):
    """
    Simple authenticated-style health check inside the versioned API namespace.

    Cloud load balancers typically hit /health at the root instead,
    but this endpoint is useful for frontend apps to verify API connectivity.
    """
    return {
        "message": "pong",
        "environment": settings.ENVIRONMENT,
    }
