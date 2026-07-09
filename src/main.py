"""
Lipika FastAPI Application Entry Point
======================================

This module is the single front door for the Lipika backend.  Uvicorn and
Gunicorn both import `app` from here:

    uvicorn src.main:app --reload
    gunicorn -k uvicorn.workers.UvicornWorker src.main:app

Everything else lives in focused sub-packages so this file stays readable.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from src.api.router import api_router
from src.core.config import Settings
from src.core.exceptions import register_exception_handlers
from src.core.lifespan import lifespan
from src.core.logging_config import setup_logging
from src.middleware.logging import StructuredLoggingMiddleware
from src.middleware.rate_limit import setup_rate_limiting


def create_application(settings: Settings | None = None) -> FastAPI:
    """
    Application Factory — builds and configures a FastAPI instance.

    Why a factory instead of `app = FastAPI()` at module level?
    ─────────────────────────────────────────────────────────────
    • Tests can call create_application() with overridden settings without
      mutating a global singleton.
    • Multiple app instances (e.g. separate test vs. prod configs) can
      coexist in the same process.
    • Configuration is explicit: every dependency flows through `settings`.

    Args:
        settings: Optional Settings override (used in tests).  Defaults to
                  loading from environment variables and .env.

    Returns:
        A fully configured FastAPI application ready for Uvicorn/Gunicorn.
    """
    if settings is None:
        settings = Settings()

    # ── 1. Structured logging (Must run before anything else logs) ──────────
    setup_logging(json_logs=settings.is_production)

    # ── 2. FastAPI instance with conditional OpenAPI docs ───────────────────
    #
    # In production we set docs_url/redoc_url/openapi_url to None so attackers
    # cannot scrape /docs or /openapi.json to map every endpoint and schema.
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )

    # Stash settings on app.state for dependency injection via SettingsDep.
    application.state.settings = settings

    # ── 3. Global exception handlers (standardized JSON error responses) ────
    register_exception_handlers(application)

    # ── 4. Middleware stack ─────────────────────────────────────────────────
    #
    # Starlette applies middleware in REVERSE order of registration:
    #   last added  → runs FIRST on incoming requests
    #   first added → runs LAST  on incoming requests
    #
    # Desired request flow (outer → inner):
    #   CORS → Rate Limit → Logging → GZip → Trusted Host → Route Handler
    #
    # So we register in the opposite order (inner → outer):

    # [Innermost] Trusted Host — rejects requests with spoofed Host headers.
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )

    # GZip — compresses large JSON/text responses to save bandwidth.
    # minimum_size=500 avoids compressing tiny responses where overhead > savings.
    application.add_middleware(GZipMiddleware, minimum_size=500)

    # Structured logging — assigns a request_id and logs timing for every call.
    application.add_middleware(StructuredLoggingMiddleware)

    # Rate limiting — caps requests per IP/minute (protects AI endpoints & bills).
    setup_rate_limiting(application, settings)

    # [Outermost] CORS — must be outermost so preflight OPTIONS requests are
    # handled before any other middleware can reject them.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── 5. Prometheus metrics (/metrics) ────────────────────────────────────
    #
    # Exposes request count, latency histograms, and in-progress gauges in
    # Prometheus text format.  Point Grafana at this endpoint for dashboards.
    if settings.METRICS_ENABLED:
        Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            excluded_handlers=["/metrics", "/health"],
        ).instrument(application).expose(
            application,
            endpoint="/metrics",
            include_in_schema=False,  # hide from public OpenAPI docs
        )

    # ── 6. Root-level routes ────────────────────────────────────────────────

    @application.get("/health", tags=["Health"], include_in_schema=False)
    async def health_check():
        """
        Lightweight liveness probe for cloud providers (AWS, Render, K8s).

        Load balancers ping this every few seconds.  Keep it fast — no DB calls.
        Return 200 + {"status": "ok"} or the container gets restarted.
        """
        return {"status": "ok"}

    @application.get("/", tags=["Root"])
    async def read_root():
        """Welcome endpoint — useful for quick sanity checks in the browser."""
        return {
            "message": f"Welcome to {settings.PROJECT_NAME}!",
            "version": settings.VERSION,
            "docs": "/docs" if settings.docs_enabled else "disabled in production",
        }

    # ── 7. Versioned API router bundle ────────────────────────────────────
    #
    # All feature endpoints live under /api/v1/... keeping URLs versioned so
    # you can ship /api/v2/ later without breaking existing clients.
    application.include_router(api_router, prefix=settings.API_V1_STR)

    return application


# ── Application instance for Uvicorn / Gunicorn ─────────────────────────────
#
# ASGI servers look for a module-level variable named `app`.
# create_application() is the factory; `app` is the production-ready output.
app = create_application()


# =============================================================================
# ARCHITECTURE GUIDE — How This Application Is Organized
# =============================================================================
#
# This section is your learning reference.  Read it top-to-bottom once, then
# use it as a map whenever you add new features.
#
# ── Directory Layout ────────────────────────────────────────────────────────
#
#   src/
#   ├── main.py                  ← YOU ARE HERE — factory + app instance
#   ├── core/
#   │   ├── config.py            ← Settings (env vars, .env file)
#   │   ├── lifespan.py          ← Startup/shutdown resource management
#   │   ├── exceptions.py        ← Global JSON error handlers
#   │   └── logging_config.py    ← structlog setup (JSON in prod, pretty in dev)
#   ├── db/
#   │   ├── base.py              ← SQLAlchemy DeclarativeBase
#   │   ├── session.py           ← Async engine + session factory
#   │   └── models/              ← One file per database table
#   ├── services/
#   │   ├── redis_client.py      ← Optional Redis connection
#   │   └── ai_client.py         ← Optional OpenAI client
#   ├── schemas/                 ← Pydantic request/response models
#   ├── middleware/
#   │   ├── logging.py           ← Per-request structured logging + request_id
#   │   └── rate_limit.py        ← SlowAPI rate limiting per IP
#   └── api/
#       ├── deps.py              ← FastAPI Depends() injection helpers
#       ├── router.py            ← Master router (bundles all v1 routers)
#       └── v1/endpoints/        ← One file per feature area
#
# ── Request Lifecycle (what happens when a browser calls your API) ──────────
#
#   1. Uvicorn receives the HTTP request.
#   2. CORS middleware checks the Origin header (allows/blocks cross-origin).
#   3. Rate limiter counts requests from this IP (429 if over limit).
#   4. Logging middleware generates a request_id and starts a timer.
#   5. GZip middleware prepares to compress the response if it's large enough.
#   6. Trusted Host middleware verifies the Host header isn't spoofed.
#   7. FastAPI routes the request to the matching endpoint function.
#   8. If an exception occurs, the global handler returns clean JSON (not a traceback).
#   9. Logging middleware records status code + duration_ms and adds X-Request-ID.
#  10. Prometheus middleware records latency/count metrics (scraped at /metrics).
#
# ── Feature Checklist (what we implemented and why) ─────────────────────────
#
#   MUST HAVE
#   ✔ Application Factory (create_application) — testable, configurable app creation
#   ✔ Lifespan context manager — safe startup/shutdown of DB pools & clients
#   ✔ CORS middleware — lets React/Next.js frontends call this API
#   ✔ Global router inclusion — /api/v1/... registers all versioned endpoints
#   ✔ Dynamic docs toggles — /docs hidden in production
#
#   INDUSTRY STANDARD
#   ✔ Global exception handlers — consistent {"error": {"code", "message"}} JSON
#   ✔ GZip middleware — compresses large responses
#   ✔ Trusted Host middleware — blocks Host header injection attacks
#   ✔ /health endpoint — cloud liveness probes
#
#   NICE EXTRA LAYER
#   ✔ Structured logging middleware — JSON logs with request_id (structlog)
#   ✔ Rate limiting middleware — caps requests per IP (SlowAPI + Redis storage)
#   ✔ Prometheus metrics — /metrics for Grafana dashboards
#
#   FULL STACK (database, cache, AI)
#   ✔ SQLAlchemy async database — engine, sessions, auto-create tables
#   ✔ Redis client — optional caching + shared rate-limit store
#   ✔ OpenAI client — optional AI endpoints with bill protection
#   ✔ Dependency injection — DBSession, RedisClient, AIClient in api/deps.py
#   ✔ Readiness probe — GET /api/v1/health/ready checks DB + Redis
#   ✔ Example CRUD — GET/POST /api/v1/notes demonstrates the full DB flow
#
# ── Environment Variables (copy .env.example → .env) ───────────────────────
#
#   ENVIRONMENT=development          # development | staging | production
#   DATABASE_URL=sqlite+aiosqlite:///./lipika.db
#   REDIS_URL=                       # optional — redis://localhost:6379/0
#   OPENAI_API_KEY=                  # optional — enables /api/v1/ai/complete
#   BACKEND_CORS_ORIGINS=http://localhost:3000
#   ALLOWED_HOSTS=localhost,127.0.0.1
#   RATE_LIMIT_PER_MINUTE=60
#   METRICS_ENABLED=true
#
# ── Adding a New Endpoint (step-by-step) ────────────────────────────────────
#
#   1. Create src/db/models/my_model.py (if it needs a database table).
#   2. Import it in src/db/models/__init__.py.
#   3. Create src/schemas/my_feature.py with Pydantic request/response models.
#   4. Create src/api/v1/endpoints/my_feature.py with an APIRouter().
#   5. Register it in src/api/router.py:
#        api_router.include_router(my_feature.router, prefix="/my-feature", tags=["MyFeature"])
#   6. Restart the dev server — it appears at /api/v1/my-feature/...
#   7. Visit http://localhost:8000/docs to test interactively (dev only).
#
# ── API Endpoints (current) ─────────────────────────────────────────────────
#
#   GET  /health                         Liveness probe (no external calls)
#   GET  /api/v1/health/ready            Readiness probe (checks DB + Redis)
#   GET  /api/v1/ping                    API connectivity check
#   GET  /api/v1/notes                   List all notes
#   POST /api/v1/notes                   Create a note
#   GET  /api/v1/notes/{id}              Get one note
#   POST /api/v1/ai/complete             AI text completion (needs OPENAI_API_KEY)
#   GET  /metrics                        Prometheus metrics
#
# =============================================================================
