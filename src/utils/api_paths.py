"""Small utilities that accept Settings via dependency injection."""

from src.core.config import Settings


def build_api_path(resource: str, settings: Settings) -> str:
    """Build a versioned API path from the injected settings."""
    prefix = settings.API_V1_STR.rstrip("/")
    path = resource.lstrip("/")
    return f"{prefix}/{path}"
