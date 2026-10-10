"""Sign-in and sign-up through Yandex ID.

`state` is a short-lived JWT: role, tab, consent and the redirect. The browser cannot
change them on the way back. An empty client id closes the routes.
"""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Final, Literal
from urllib.parse import urlencode, urlsplit

import jwt
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import AdminBanEntry
from app.core.config import Settings
from app.core.errors import (
    AppError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
)
from app.core.security import hash_password
from app.integrations.yandex.client import AUTHORIZE_URL, SCOPE, YandexAccount, YandexDirectory
from app.models import User, UserRole
from app.repositories.user import UserRepository
from app.services.auth import AuthService, IssuedSession, normalize_email

STATE_TTL: Final = timedelta(minutes=10)
_STATE_TYPE: Final = "yandex_login"
CALLBACK_PATH: Final = "/auth/yandex/callback"
RoleName = Literal["candidate", "employer"]
ModeName = Literal["sign-in", "sign-up"]


class YandexAuthService:
    def __init__(
        self,
        session: AsyncSession,
        users: UserRepository,
        auth: AuthService,
        settings: Settings,
        directory: YandexDirectory,
    ) -> None:
        self._session = session
        self._users = users
        self._auth = auth
        self._settings = settings
        self._directory = directory

    def enabled(self) -> bool:
        secret = self._settings.yandex_client_secret.get_secret_value()
        return bool(self._settings.yandex_client_id.strip() and secret)

    async def start(
        self,
        *,
        role: RoleName,
        mode: ModeName,
        consent: bool,
        redirect_uri: str,
    ) -> str:
        self._require_configured()
        if mode == "sign-up" and not consent:
            raise AppError("Нужно согласие на обработку персональных данных")
        if not redirect_allowed(self._settings, redirect_uri):
            raise AppError("Адрес возврата не зарегистрирован для Яндекс ID")
        state = self._state(role=role, mode=mode, consent=consent, redirect_uri=redirect_uri)
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self._settings.yandex_client_id,
                "redirect_uri": redirect_uri,
                "state": state,
                "scope": SCOPE,
            }
        )
        return f"{AUTHORIZE_URL}?{query}"

    async def complete(self, *, code: str, state: str) -> tuple[IssuedSession, bool]:
        """Returns the session and whether this call created the account."""
        self._require_configured()
        claims = self._read_state(state)
        account = await self._directory.fetch(code=code, redirect_uri=claims["ru"])
        user, created = await self._account(account, claims)
        return await self._auth.open_session(user), created

    def _require_configured(self) -> None:
        if not self.enabled():
            raise NotFoundError()

    async def _account(self, account: YandexAccount, claims: dict[str, Any]) -> tuple[User, bool]:
        email = normalize_email(account.email)
        role = UserRole(claims["role"])
        linked = await self._users.get_by_yandex_id(account.account_id)
        if linked is not None:
            return linked, False
        existing = await self._users.get_by_email(email)
        if existing is not None:
            if existing.role != role:
                raise ConflictError("Эта почта уже зарегистрирована с другой ролью")
            if await self._blocked(email):
                raise PermissionDeniedError("Регистрация на эту почту закрыта")
            if existing.yandex_id and existing.yandex_id != account.account_id:
                raise ConflictError("Аккаунт уже связан с другим Яндекс ID")
            existing.yandex_id = account.account_id
            existing.is_email_verified = True
            _fill_names(existing, account)
            _keep_portrait(existing, account.portrait)
            return existing, False
        if claims["mode"] == "sign-in":
            raise AppError("Сначала зарегистрируйтесь")
        if await self._blocked(email):
            raise PermissionDeniedError("Регистрация на эту почту закрыта")
        user = await self._users.add(
            User(
                email=email,
                password_hash=hash_password(secrets.token_urlsafe(32)),
                role=role,
                is_email_verified=True,
                personal_data_consent=True,
                first_name=_clip(account.first_name),
                last_name=_clip(account.last_name),
                yandex_id=account.account_id,
            )
        )
        _keep_portrait(user, account.portrait)
        return user, True

    async def _blocked(self, email: str) -> bool:
        domain = email.partition("@")[2]
        found = await self._session.scalar(
            select(AdminBanEntry.id)
            .where(
                AdminBanEntry.is_active.is_(True),
                or_(
                    func.lower(AdminBanEntry.email) == email,
                    func.lower(AdminBanEntry.email_domain) == domain,
                ),
            )
            .limit(1)
        )
        return found is not None

    def _secret(self) -> str:
        return self._settings.jwt_secret.get_secret_value()

    def _state(self, *, role: RoleName, mode: ModeName, consent: bool, redirect_uri: str) -> str:
        now = datetime.now(UTC)
        payload = {
            "iss": self._settings.jwt_issuer,
            "typ": _STATE_TYPE,
            "role": role,
            "mode": mode,
            "consent": consent,
            "ru": redirect_uri,
            "nonce": secrets.token_urlsafe(16),
            "iat": now,
            "exp": now + STATE_TTL,
        }
        return jwt.encode(payload, self._secret(), algorithm=self._settings.jwt_algorithm)

    def _read_state(self, state: str) -> dict[str, Any]:
        try:
            claims: dict[str, Any] = jwt.decode(
                state,
                self._secret(),
                algorithms=[self._settings.jwt_algorithm],
                issuer=self._settings.jwt_issuer,
                options={"require": ["exp", "iss"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationError(
                "Вход через Яндекс занял слишком долго. Начните заново."
            ) from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError("Вход через Яндекс не подтверждён. Начните заново.") from exc
        valid = (
            claims.get("typ") == _STATE_TYPE
            and claims.get("role") in ("candidate", "employer")
            and claims.get("mode") in ("sign-in", "sign-up")
            and isinstance(claims.get("consent"), bool)
            and isinstance(claims.get("ru"), str)
        )
        if not valid or (claims["mode"] == "sign-up" and not claims["consent"]):
            raise AuthenticationError("Вход через Яндекс не подтверждён. Начните заново.")
        return claims


def redirect_allowed(settings: Settings, redirect_uri: str) -> bool:
    """The configured callback, the same page on a trusted origin, or this machine."""
    if redirect_uri == settings.yandex_redirect_uri:
        return True
    parts = urlsplit(redirect_uri)
    if parts.scheme not in ("http", "https") or parts.path != CALLBACK_PATH:
        return False
    if parts.query or parts.fragment:
        return False
    origin = f"{parts.scheme}://{parts.netloc}"
    if origin in settings.cors_origins:
        return True
    host = parts.hostname
    return host in ("localhost", "127.0.0.1", "::1")


def _clip(value: str) -> str | None:
    text = value.strip()
    return text[:100] or None


def _fill_names(user: User, account: YandexAccount) -> None:
    if not user.first_name:
        user.first_name = _clip(account.first_name)
    if not user.last_name:
        user.last_name = _clip(account.last_name)


def _keep_portrait(user: User, portrait: tuple[bytes, str] | None) -> None:
    """Only a specialist's resume shows «Фото». An employer card uses the name."""
    if user.role != UserRole.CANDIDATE or portrait is None or user.pending_photo_type:
        return
    user.pending_photo, user.pending_photo_type = portrait
