import hmac

from fastapi import APIRouter, Request, Response, status

from app.api.auth_cookies import (
    REFRESH_COOKIE,
    clear_refresh_cookie,
    require_csrf,
    set_refresh_cookie,
)
from app.core.errors import AuthenticationError, NotFoundError
from app.dependencies.common import SettingsDep
from app.dependencies.services import AuthServiceDep, YandexAuthServiceDep
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    ResendVerificationRequest,
    TokenResponse,
    VerifyEmailRequest,
    YandexCallbackRequest,
    YandexCallbackResponse,
    YandexStartRequest,
    YandexStartResponse,
    YandexStatusResponse,
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


def _same_secret(provided: str, expected: str) -> bool:
    if not provided or not expected:
        return False
    try:
        return hmac.compare_digest(provided.encode(), expected.encode())
    except (TypeError, ValueError):
        return False


@router.post(
    "/admin-gate",
    summary="Open the admin session after the browser accepted the nginx password",
)
async def admin_gate(
    request: Request, auth: AuthServiceDep, settings: SettingsDep, response: Response
) -> TokenResponse:
    expected = settings.admin_gate_secret.get_secret_value()
    if not expected or not settings.admin_email.strip():
        raise NotFoundError()
    if not _same_secret(request.headers.get("x-admin-gate", ""), expected):
        raise AuthenticationError("Вход в админку закрыт")
    issued = await auth.open_admin_gate(settings.admin_email)
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


@router.get("/yandex", summary="Whether the Yandex ID button is available")
async def yandex_status(yandex: YandexAuthServiceDep) -> YandexStatusResponse:
    if not yandex.enabled():
        raise NotFoundError()
    return YandexStatusResponse()


@router.post("/yandex/start", summary="Begin Yandex ID sign-in or sign-up")
async def yandex_start(
    data: YandexStartRequest, yandex: YandexAuthServiceDep
) -> YandexStartResponse:
    url = await yandex.start(
        role=data.role,
        mode=data.mode,
        consent=data.personal_data_consent,
        redirect_uri=data.redirect_uri,
    )
    return YandexStartResponse(authorize_url=url)


@router.post("/yandex/callback", summary="Exchange the Yandex code for a session")
async def yandex_callback(
    data: YandexCallbackRequest,
    yandex: YandexAuthServiceDep,
    settings: SettingsDep,
    response: Response,
) -> YandexCallbackResponse:
    issued, created = await yandex.complete(code=data.code, state=data.state)
    set_refresh_cookie(response, issued.refresh_token, issued.refresh_ttl, settings)
    token = issued.response
    return YandexCallbackResponse(
        access_token=token.access_token,
        expires_in=token.expires_in,
        user=token.user,
        created=created,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke the refresh cookie")
async def logout(
    request: Request, auth: AuthServiceDep, settings: SettingsDep, response: Response
) -> None:
    require_csrf(request)
    await auth.logout(request.cookies.get(REFRESH_COOKIE))
    clear_refresh_cookie(response, settings)
