from app.core.config import Settings
from app.core.errors import AuthenticationError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead


def normalize_email(email: str) -> str:
    return email.strip().lower()


class AuthService:
    def __init__(self, users: UserRepository, settings: Settings) -> None:
        self._users = users
        self._settings = settings

    async def register(self, data: RegisterRequest) -> User:
        email = normalize_email(str(data.email))
        if await self._users.get_by_email(email):
            raise ConflictError("Пользователь с таким email уже зарегистрирован")

        # TODO(auth): send an email confirmation link (ТЗ 2.2, item 4) and set is_email_verified
        # only after the link is opened. Needs an SMTP provider decision.
        return await self._users.add(
            User(
                email=email,
                password_hash=hash_password(data.password),
                role=UserRole(data.role),
                personal_data_consent=data.personal_data_consent,
            )
        )

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self._users.get_by_email(normalize_email(str(data.email)))
        # Same error for unknown email and wrong password: don't reveal registered accounts.
        if not verify_password(data.password, user.password_hash if user else None) or not user:
            raise AuthenticationError("Неверный email или пароль")
        if not user.is_active:
            raise AuthenticationError("Учётная запись заблокирована")

        token, expires_in = create_access_token(
            subject=str(user.id), email=user.email, roles=[user.role.value], settings=self._settings
        )
        return TokenResponse(
            access_token=token, expires_in=expires_in, user=UserRead.model_validate(user)
        )
