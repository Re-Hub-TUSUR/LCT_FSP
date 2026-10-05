import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from app.core.config import Settings
from app.core.errors import (
    AuthenticationError,
    ConflictError,
    EmailNotVerifiedError,
    TooManyRequestsError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models import EmailVerificationCode, User, UserRole
from app.repositories.email_verification import EmailVerificationRepository
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.email import CODE_TTL_MINUTES, EmailSender

CODE_LENGTH = 6
RESEND_COOLDOWN = timedelta(seconds=60)
MAX_ATTEMPTS = 5


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


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        codes: EmailVerificationRepository,
        settings: Settings,
        mailer: EmailSender,
    ) -> None:
        self._users = users
        self._codes = codes
        self._settings = settings
        self._mailer = mailer

    async def register(self, data: RegisterRequest) -> User:
        email = normalize_email(str(data.email))
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

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self._users.get_by_email(normalize_email(str(data.email)))
        # Same error for unknown email and wrong password: don't reveal registered accounts.
        if not verify_password(data.password, user.password_hash if user else None) or not user:
            raise AuthenticationError("Неверный email или пароль")
        if not user.is_active:
            raise AuthenticationError("Учётная запись заблокирована")
        if not user.is_email_verified:
            try:
                await self._issue_code(user, respect_cooldown=True)
                await self._codes.commit()
            except TooManyRequestsError:
                pass
            raise EmailNotVerifiedError(details={"email": user.email})

        token, expires_in = create_access_token(
            subject=str(user.id), email=user.email, roles=[user.role.value], settings=self._settings
        )
        return TokenResponse(
            access_token=token, expires_in=expires_in, user=UserRead.model_validate(user)
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
