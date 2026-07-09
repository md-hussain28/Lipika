"""
AI completion endpoint — demonstrates optional OpenAI client usage.

Requires OPENAI_API_KEY in .env. Returns 503 when AI is not configured.
Rate-limited tighter than default (10/min) to protect your API bill.
"""

from fastapi import APIRouter, Request

from src.api.deps import RequiredAIClient, SettingsDep
from src.middleware.rate_limit import limiter
from src.schemas.ai import AICompletionRequest, AICompletionResponse

router = APIRouter()


@router.post("/complete", response_model=AICompletionResponse)
@limiter.limit("10/minute")
async def complete(
    request: Request,
    body: AICompletionRequest,
    ai_client: RequiredAIClient,
    settings: SettingsDep,
):
    """
    Send a prompt to OpenAI and return the model's text response.

    SlowAPI requires `request: Request` in the signature when using @limiter.limit.
    """
    response = await ai_client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": body.prompt}],
        max_tokens=500,
    )
    content = response.choices[0].message.content or ""
    return AICompletionResponse(model=settings.OPENAI_MODEL, content=content)
