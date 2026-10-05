from typing import Literal

from pydantic import EmailStr, Field

from app.schemas.common import ApiModel
from app.schemas.user import UserRead

PASSWORD_MIN_LENGTH = 8


class RegisterRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)
    # Admin accounts are never self-registered.
    role: Literal["candidate", "employer"]
    # 152-ФЗ: explicit consent to personal data processing is required.
    personal_data_consent: Literal[True]


class LoginRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(ApiModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105 - OAuth2 scheme name, not a secret
    expires_in: int
    user: UserRead
