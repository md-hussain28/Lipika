from fastapi import APIRouter, HTTPException, Request, Response, status

from src.api.deps.auth import RegisterServiceDep
from src.schemas.auth import UserRead, UserRegisterRequest
from src.services.auth.exceptions import EmailAlreadyRegisteredError

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: UserRegisterRequest,
    register_service: RegisterServiceDep,
) -> UserRead:
    """Create a new user account."""
    try:
        user = await register_service.register(body)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return UserRead.model_validate(user)


@router.post("/login")
async def login(request: Request, response: Response):
    return {"message": "Hello, World!"}


@router.post("/logout")
async def logout(request: Request, response: Response):
    return {"message": "Hello, World!"}
