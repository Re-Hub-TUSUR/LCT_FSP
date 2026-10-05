from fastapi import APIRouter, status

from app.api.stub import not_implemented
from app.dependencies.services import AuthServiceDep
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    ResendVerificationRequest,
    TokenResponse,
    VerifyEmailRequest,
)
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
    "/verify-email",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Confirm email with the 6-digit code",
)
async def verify_email(data: VerifyEmailRequest, auth: AuthServiceDep) -> None:
    await auth.verify_email(str(data.email), data.code)


@router.post(
    "/resend-verification",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Send a new 6-digit code (60s cooldown)",
)
async def resend_verification(data: ResendVerificationRequest, auth: AuthServiceDep) -> None:
    await auth.resend_verification(str(data.email))


@router.post("/refresh", summary="Rotate access token using an httpOnly refresh cookie")
async def refresh() -> TokenResponse:
    not_implemented("auth.refresh")
