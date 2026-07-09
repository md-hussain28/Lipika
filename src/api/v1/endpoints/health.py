"""
Readiness probe — checks that backing services are actually reachable.

Cloud platforms use two health checks:
  • Liveness  (/health)        — is the process alive? (no external calls)
  • Readiness (/health/ready)  — can it serve traffic? (checks DB, Redis, etc.)

If readiness fails, the load balancer stops sending traffic until it recovers.
"""

from fastapi import APIRouter, Request, Response, status
from sqlalchemy import text

router = APIRouter()


@router.get("/ready")
async def readiness_check(request: Request, response: Response):
    """
    Verify database (and optionally Redis) connectivity.

    Returns 200 when all configured services respond, 503 otherwise.
    """
    checks: dict[str, str] = {}
    all_ok = True

    # Database — always required
    try:
        session_factory = request.app.state.db_session_factory
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        all_ok = False

    # Redis — only checked when configured
    redis = request.app.state.redis
    if redis is not None:
        try:
            await redis.ping()
            checks["redis"] = "ok"
        except Exception as exc:
            checks["redis"] = f"error: {exc}"
            all_ok = False
    else:
        checks["redis"] = "disabled"

    checks["ai"] = "ok" if request.app.state.ai_client else "disabled"

    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"status": "ok" if all_ok else "degraded", "checks": checks}
