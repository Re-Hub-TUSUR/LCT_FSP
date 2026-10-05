from fastapi import APIRouter, status

from app.api.stub import not_implemented
from app.dependencies.services import AuthServiceDep
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.common import ErrorResponse
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a candidate or an employer by email",
    responses={409: {"model": ErrorResponse, "description": "Email уже зарегистрирован"}},
)
async def register(data: RegisterRequest, auth: AuthServiceDep) -> UserRead:
    return UserRead.model_validate(await auth.register(data))


@router.post("/login", summary="Exchange email + password for a JWT access token")
async def login(data: LoginRequest, auth: AuthServiceDep) -> TokenResponse:
    return await auth.login(data)


@router.post(
    "/verify-email", status_code=status.HTTP_204_NO_CONTENT, summary="Confirm email by token"
)
async def verify_email(token: str) -> None:
    not_implemented("auth.verify_email")


@router.post("/refresh", summary="Rotate access token using an httpOnly refresh cookie")
async def refresh() -> TokenResponse:
    not_implemented("auth.refresh")
