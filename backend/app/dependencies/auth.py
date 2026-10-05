import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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


def require_roles(*roles: UserRole) -> Callable[[User], Awaitable[User]]:
    """Role guard. Role is re-read from the DB on every request, not trusted from the token."""

    async def dependency(user: CurrentUser) -> User:
        if user.role not in roles:
            raise PermissionDeniedError()
        return user

    return dependency


CandidateUser = Annotated[User, Depends(require_roles(UserRole.CANDIDATE))]
EmployerUser = Annotated[User, Depends(require_roles(UserRole.EMPLOYER))]
AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN))]
