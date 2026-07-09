"""
Application settings loaded from environment variables and .env files.

Pydantic Settings validates types at startup so misconfiguration fails fast
instead of causing cryptic runtime errors in production.
"""

from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration object — every module reads from here."""

    # ── App identity ──────────────────────────────────────────────────────
    PROJECT_NAME: str = "Lipika Backend API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # ── API routing ───────────────────────────────────────────────────────
    API_V1_STR: str = "/api/v1"

    # ── Database ────────────────────────────────────────────────────────────
    # Dev default uses local SQLite — zero setup required.
    # Production: postgresql+asyncpg://user:pass@localhost:5432/lipika
    DATABASE_URL: str = "sqlite+aiosqlite:///./lipika.db"
    DATABASE_ECHO: bool = False  # True prints every SQL statement (dev debugging)

    # ── Redis (optional) ────────────────────────────────────────────────────
    # Leave empty to run without Redis. Example: redis://localhost:6379/0
    REDIS_URL: str = ""

    # ── OpenAI (optional) ───────────────────────────────────────────────────
    OPENAI_API_KEY: SecretStr | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── Security ────────────────────────────────────────────────────────────
    # Comma-separated in .env: BACKEND_CORS_ORIGINS=http://localhost:3000,https://app.example.com
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    # Only requests whose Host header matches one of these values are accepted.
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]

    # ── Rate limiting ───────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── Observability ───────────────────────────────────────────────────────
    # Set to False in production if /metrics should only be reachable internally.
    METRICS_ENABLED: bool = True

    # ── Pydantic config ─────────────────────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Field validators ────────────────────────────────────────────────────

    @field_validator("BACKEND_CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_comma_separated_strings(cls, value: str | list[str]) -> list[str]:
        """Parse comma-separated strings from .env into clean lists."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("OPENAI_API_KEY", mode="before")
    @classmethod
    def empty_api_key_to_none(cls, value: str | SecretStr | None) -> str | None:
        """Treat unset or blank OPENAI_API_KEY as disabled (same as leaving .env empty)."""
        if value is None:
            return None
        if isinstance(value, SecretStr):
            value = value.get_secret_value()
        if isinstance(value, str) and not value.strip():
            return None
        return value

    # ── Model validators ────────────────────────────────────────────────────

    @model_validator(mode="after")
    def validate_production_defaults(self) -> "Settings":
        """Fail fast if production launches with local dev defaults."""
        if self.ENVIRONMENT == "production":
            if "sqlite" in self.DATABASE_URL.lower():
                raise ValueError(
                    "CRITICAL: Cannot use SQLite in a production environment!"
                )
            if "localhost" in self.ALLOWED_HOSTS or "127.0.0.1" in self.ALLOWED_HOSTS:
                raise ValueError(
                    "CRITICAL: Localhost cannot be in ALLOWED_HOSTS during production!"
                )
        return self

    # ── Computed properties ─────────────────────────────────────────────────

    @property
    def is_production(self) -> bool:
        """Shortcut used throughout the app to branch on environment."""
        return self.ENVIRONMENT == "production"

    @property
    def docs_enabled(self) -> bool:
        """
        OpenAPI docs (/docs, /redoc) are a security risk in production —
        they expose your entire API surface to anyone who finds the URL.
        """
        return not self.is_production

    @property
    def redis_enabled(self) -> bool:
        return bool(self.REDIS_URL)

    @property
    def ai_enabled(self) -> bool:
        return self.OPENAI_API_KEY is not None
