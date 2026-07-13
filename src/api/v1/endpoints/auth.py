from fastapi import APIRouter, Request, Response, status

from src.db.models.user import User
from src.schemas.auth import UserRegisterRequest
router = APIRouter()

@router.post("/register")
async def register(user: UserRegisterRequest,request: Request, response: Response):
    body = await request.body()
    print("Body:------>", body, "User:------>", user)
    return {"body": "hello"}


@router.post("/login")
async def login(request: Request, response: Response):
    return {"message": "Hello, World!"}

@router.post("/logout")
async def logout(request: Request, response: Response):
    return {"message": "Hello, World!"}