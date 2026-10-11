import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.admin.services.banlist import active_ban_for, active_ban_for_email, raise_if_banned
from app.core.config import Settings
from app.core.errors import (
    AuthenticationError,
    ConflictError,
    EmailNotVerifiedError,
    TooManyRequestsError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models import EmailVerificationCode, RefreshToken, User, UserRole
from app.repositories.email_verification import EmailVerificationRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.email import CODE_TTL_MINUTES, EmailSender

CODE_LENGTH = 6
RESEND_COOLDOWN = timedelta(seconds=60)
MAX_ATTEMPTS = 5
# Activity is a filter by days: one write per hour is precise enough.
ACTIVITY_STEP = timedelta(hours=1)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _new_code(settings: Settings) -> str:
    # Tests assert against this fixed code. Every other environment gets a random one.
    if settings.app_env == "test":
        return "000000"
    return f"{secrets.randbelow(10**CODE_LENGTH):0{CODE_LENGTH}d}"


def _hash_code(code: str, settings: Settings) -> str:
    return hmac.new(
        settings.jwt_secret.get_secret_value().encode(), code.encode(), hashlib.sha256
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class IssuedSession:
    response: TokenResponse
    refresh_token: str
    refresh_ttl: int


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        codes: EmailVerificationRepository,
        refresh_tokens: RefreshTokenRepository,
        settings: Settings,
        mailer: EmailSender,
    ) -> None:
        self._users = users
        self._codes = codes
        self._refresh_tokens = refresh_tokens
        self._settings = settings
        self._mailer = mailer

    async def register(self, data: RegisterRequest) -> User:
        email = normalize_email(str(data.email))
        raise_if_banned(await active_ban_for_email(self._users._session, email), self._settings)
        if await self._users.get_by_email(email):
            raise ConflictError("Пользователь с таким email уже зарегистрирован")

        user = await self._users.add(
            User(
                email=email,
                password_hash=hash_password(data.password),
                role=UserRole(data.role),
                personal_data_consent=data.personal_data_consent,
            )
        )
        await self._issue_code(user)
        return user

    async def login(self, data: LoginRequest) -> IssuedSession:
        user = await self._users.get_by_email(normalize_email(str(data.email)))
        # Same error for unknown email and wrong password: don't reveal registered accounts.
        if not verify_password(data.password, user.password_hash if user else None) or not user:
            raise AuthenticationError("Неверный email или пароль")
        raise_if_banned(await active_ban_for(self._users._session, user), self._settings)
        if not user.is_active:
            raise AuthenticationError("Учётная запись заблокирована")
        if not user.is_email_verified:
            try:
                await self._issue_code(user, respect_cooldown=True)
                await self._codes.commit()
            except TooManyRequestsError:
                pass
            raise EmailNotVerifiedError(details={"email": user.email})
        return await self._open_session(user)

    async def open_admin_gate(self, email: str) -> IssuedSession:
        """Session for the administrator the nginx gate already let through."""
        user = await self._users.get_by_email(normalize_email(email))
        if user is None or user.role != UserRole.ADMIN or not user.is_email_verified:
            raise AuthenticationError("Вход в админку закрыт")
        raise_if_banned(await active_ban_for(self._users._session, user), self._settings)
        if not user.is_active:
            raise AuthenticationError("Учётная запись заблокирована")
        return await self._open_session(user)

    async def open_session(self, user: User) -> IssuedSession:
        """Session for a person Yandex ID already proved. The caller checked the account."""
        raise_if_banned(await active_ban_for(self._users._session, user), self._settings)
        if not user.is_active:
            raise AuthenticationError("Учётная запись заблокирована")
        return await self._open_session(user)

    async def refresh(self, raw_token: str) -> IssuedSession:
        claims = decode_refresh_token(raw_token, self._settings)
        try:
            subject = uuid.UUID(claims.subject)
        except ValueError as exc:
            raise AuthenticationError("Сессия недействительна") from exc
        user = await self._users.get_by_id(subject)
        # A revoked cookie of a banned account still explains the ban, instead of a bare 401.
        if user is not None:
            raise_if_banned(await active_ban_for(self._users._session, user), self._settings)
        stored = await self._refresh_tokens.get(claims.token_id)
        now = datetime.now(UTC)
        if (
            user is None
            or stored is None
            or stored.revoked_at is not None
            or _aware(stored.expires_at) < now
            or stored.user_id != subject
            or not user.is_active
        ):
            raise AuthenticationError("Сессия недействительна")
        # Two requests with one cookie: only the one that revokes it gets a new session.
        if not await self._refresh_tokens.revoke(stored.id, now):
            raise AuthenticationError("Сессия недействительна")
        return await self._open_session(user)

    async def logout(self, raw_token: str | None) -> None:
        if not raw_token:
            return
        try:
            claims = decode_refresh_token(raw_token, self._settings)
        except AuthenticationError:
            return
        stored = await self._refresh_tokens.get(claims.token_id)
        if stored is not None and stored.revoked_at is None:
            stored.revoked_at = datetime.now(UTC)

    async def _open_session(self, user: User) -> IssuedSession:
        now = datetime.now(UTC)
        if user.last_active_at is None or now - _aware(user.last_active_at) >= ACTIVITY_STEP:
            user.last_active_at = now
        token, expires_in = create_access_token(
            subject=str(user.id), email=user.email, roles=[user.role.value], settings=self._settings
        )
        token_id = uuid.uuid4()
        refresh, refresh_ttl = create_refresh_token(
            subject=str(user.id), token_id=token_id, settings=self._settings
        )
        await self._refresh_tokens.add(
            RefreshToken(
                id=token_id,
                user_id=user.id,
                expires_at=datetime.now(UTC) + timedelta(seconds=refresh_ttl),
            )
        )
        return IssuedSession(
            response=TokenResponse(
                access_token=token, expires_in=expires_in, user=UserRead.model_validate(user)
            ),
            refresh_token=refresh,
            refresh_ttl=refresh_ttl,
        )

    async def verify_email(self, email: str, code: str) -> None:
        user = await self._users.get_by_email(normalize_email(email))
        if user is None or user.is_email_verified:
            raise AuthenticationError("Неверный код")

        stored = await self._codes.get_for_user(user.id)
        now = datetime.now(UTC)
        if stored is None or _aware(stored.expires_at) < now:
            raise AuthenticationError("Срок действия кода истёк. Запросите новый.")

        if not hmac.compare_digest(stored.code_hash, _hash_code(code, self._settings)):
            stored.attempts += 1
            if stored.attempts >= MAX_ATTEMPTS:
                await self._codes.delete(stored)
            # The error below rolls the request back, so the counter has to be committed on its own.
            await self._codes.commit()
            if stored.attempts >= MAX_ATTEMPTS:
                raise AuthenticationError("Слишком много попыток. Запросите новый код.")
            raise AuthenticationError("Неверный код")

        user.is_email_verified = True
        await self._codes.delete(stored)

    async def resend_verification(self, email: str) -> None:
        user = await self._users.get_by_email(normalize_email(email))
        if user is None or user.is_email_verified:
            return
        await self._issue_code(user, respect_cooldown=True)

    async def _issue_code(self, user: User, *, respect_cooldown: bool = False) -> None:
        now = datetime.now(UTC)
        stored = await self._codes.get_for_user(user.id)
        if respect_cooldown and stored is not None:
            elapsed = now - _aware(stored.sent_at)
            if elapsed < RESEND_COOLDOWN:
                wait = int((RESEND_COOLDOWN - elapsed).total_seconds()) + 1
                raise TooManyRequestsError(f"Повторная отправка через {wait} с")

        code = _new_code(self._settings)
        if stored is None:
            await self._codes.add(
                EmailVerificationCode(
                    user_id=user.id,
                    code_hash=_hash_code(code, self._settings),
                    expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
                    sent_at=now,
                    attempts=0,
                )
            )
        else:
            stored.code_hash = _hash_code(code, self._settings)
            stored.expires_at = now + timedelta(minutes=CODE_TTL_MINUTES)
            stored.sent_at = now
            stored.attempts = 0

        await self._mailer.send_verification_code(to=user.email, code=code)
