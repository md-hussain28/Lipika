"""Schemas for the Notes feature."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    """Body for POST /notes."""

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(default="")


class NoteRead(BaseModel):
    """Response shape for a single note."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
