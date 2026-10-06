from fastapi import APIRouter, Request, Response, status

from app.api.auth_cookies import (
    REFRESH_COOKIE,
    clear_refresh_cookie,
    require_csrf,
    set_refresh_cookie,
)
from app.core.errors import AuthenticationError
from app.dependencies.common import SettingsDep
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
async def login(
    data: LoginRequest, auth: AuthServiceDep, settings: SettingsDep, response: Response
) -> TokenResponse:
    issued = await auth.login(data)
    set_refresh_cookie(response, issued.refresh_token, issued.refresh_ttl, settings)
    return issued.response


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


@router.post("/refresh", summary="Rotate the session and return a fresh access token")
async def refresh(
    request: Request, auth: AuthServiceDep, settings: SettingsDep, response: Response
) -> TokenResponse:
    require_csrf(request)
    raw = request.cookies.get(REFRESH_COOKIE)
    if not raw:
        raise AuthenticationError("Сессия не найдена")
    issued = await auth.refresh(raw)
    set_refresh_cookie(response, issued.refresh_token, issued.refresh_ttl, settings)
    return issued.response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke the refresh cookie")
async def logout(
    request: Request, auth: AuthServiceDep, settings: SettingsDep, response: Response
) -> None:
    require_csrf(request)
    await auth.logout(request.cookies.get(REFRESH_COOKIE))
    clear_refresh_cookie(response, settings)
