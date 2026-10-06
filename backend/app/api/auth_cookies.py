"""Refresh cookie. The access JWT is in the JSON body; this token is hidden from scripts."""

from fastapi import Request, Response

from app.core.config import Settings
from app.core.errors import AuthenticationError

REFRESH_COOKIE = "kadry_refresh"
# Only the auth routes need the cookie, so it is not attached to every API call.
REFRESH_PATH = "/api/v1/auth"
# A cross-site form cannot set a custom header. Combined with SameSite=Lax this blocks CSRF.
CSRF_HEADER = "x-kadry-request"
CSRF_VALUE = "1"


def set_refresh_cookie(response: Response, token: str, max_age: int, settings: Settings) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path=REFRESH_PATH,
    )


def require_csrf(request: Request) -> None:
    if request.headers.get(CSRF_HEADER) != CSRF_VALUE:
        raise AuthenticationError("Запрос отклонён")


def clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path=REFRESH_PATH,
    )
