"""
OpenAI async client factory — optional AI integration.

Like Redis, the AI client is optional. Without OPENAI_API_KEY the app still
starts; AI routes return 503 Service Unavailable instead of crashing at boot.
"""

from openai import AsyncOpenAI

from src.core.config import Settings


def create_ai_client(settings: Settings) -> AsyncOpenAI | None:
    """
    Instantiate the OpenAI SDK client if an API key is present.

    The client is long-lived (created once at startup) and reused across requests.
    """
    if not settings.OPENAI_API_KEY:
        return None

    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())
