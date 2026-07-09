"""Pydantic request/response schemas for the API layer."""

from src.schemas.ai import AICompletionRequest, AICompletionResponse
from src.schemas.note import NoteCreate, NoteRead

__all__ = [
    "NoteCreate",
    "NoteRead",
    "AICompletionRequest",
    "AICompletionResponse",
]
