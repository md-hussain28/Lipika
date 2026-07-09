"""Schemas for AI endpoints."""

from pydantic import BaseModel, Field


class AICompletionRequest(BaseModel):
    """Body for POST /ai/complete."""

    prompt: str = Field(..., min_length=1, max_length=4000)


class AICompletionResponse(BaseModel):
    """Response from the AI completion endpoint."""

    model: str
    content: str
