from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="The email of the user")
    password: str = Field(..., description="The password of the user")
    confirm_password: str = Field(..., description="The confirm password of the user")
