"""
Master API router — bundles all versioned endpoint routers.

As your app grows, add new routers here:
    from src.api.v1.endpoints import users, items
    api_router.include_router(users.router, prefix="/users", tags=["Users"])
"""

from fastapi import APIRouter

from src.api.v1.endpoints import ai, health, notes, ping, auth

api_router = APIRouter()

api_router.include_router(ping.router, tags=["Utility"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(notes.router, prefix="/notes", tags=["Notes"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])