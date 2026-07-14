"""Schemas for authentication endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from pydantic_core import PydanticCustomError


class UserRegisterRequest(BaseModel):
    """Body for POST /auth/register."""

    email: EmailStr = Field(..., description="The email of the user")
    password: str = Field(
        ..., min_length=8, max_length=128, description="The password of the user"
    )
    confirm_password: str = Field(
        ..., min_length=8, max_length=128, description="Must match password"
    )

    @model_validator(mode="after")
    def passwords_match(self) -> "UserRegisterRequest":
        if self.password != self.confirm_password:
            raise PydanticCustomError(
                "password_mismatch",
                "Password and confirm password do not match",
            )
        return self


class UserRead(BaseModel):
    """Public user profile returned after registration."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    is_active: bool
    created_at: datetime
