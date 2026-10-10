import hmac
import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings
from app.core.errors import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token
from app.dependencies.common import SessionDep, SettingsDep
from app.models import User, UserRole
from app.repositories.user import UserRepository

_bearer = HTTPBearer(auto_error=False, description="JWT access token from POST /auth/login")


async def get_current_user(
    session: SessionDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise AuthenticationError()
    claims = decode_access_token(credentials.credentials, settings)
    try:
        user_id = uuid.UUID(claims.subject)
    except ValueError as exc:
        raise AuthenticationError("Недействительный токен") from exc

    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_optional_user(
    session: SessionDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User | None:
    """Public endpoints: anonymous without a token, but a bad token is still a 401."""
    if credentials is None:
        return None
    return await get_current_user(session, settings, credentials)


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def require_roles(*roles: UserRole) -> Callable[[User], Awaitable[User]]:
    """Role guard. Role is re-read from the DB on every request, not trusted from the token."""

    async def dependency(user: CurrentUser) -> User:
        if user.role not in roles:
            raise PermissionDeniedError()
        return user

    return dependency


def same_secret(provided: str, expected: str) -> bool:
    if not provided or not expected:
        return False
    try:
        return hmac.compare_digest(provided.encode(), expected.encode())
    except (TypeError, ValueError):
        return False


def through_admin_gate(request: Request, settings: Settings) -> bool:
    """The request came through the admin proxy: only it sets the gate header, and the public
    nginx drops one sent by a client. Without a configured gate (development, tests) there is
    no proxy in front, so nothing to check."""
    expected = settings.admin_gate_secret.get_secret_value()
    if not expected or not settings.is_production:
        return True
    return same_secret(request.headers.get("x-admin-gate", ""), expected)


async def get_admin_user(request: Request, settings: SettingsDep, user: CurrentUser) -> User:
    """An admin token alone is not enough: a stolen password or token must not open the admin
    API from the public site, past the gate's own password."""
    if user.role != UserRole.ADMIN:
        raise PermissionDeniedError()
    if not through_admin_gate(request, settings):
        raise PermissionDeniedError("Админка открывается только через её адрес")
    return user


CandidateUser = Annotated[User, Depends(require_roles(UserRole.CANDIDATE))]
EmployerUser = Annotated[User, Depends(require_roles(UserRole.EMPLOYER))]
AdminUser = Annotated[User, Depends(get_admin_user)]
