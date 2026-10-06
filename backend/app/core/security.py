"""Password hashing and JWT access / refresh tokens.

Token claims follow the OIDC / Keycloak shape (`sub`, `email`, `realm_access.roles`) so that the
future FSP ID (Keycloak) tokens can be validated by the same dependency with an RS256 key.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings
from app.core.errors import AuthenticationError

_password_hash = PasswordHash.recommended()  # Argon2id

# Verified when the user does not exist, so login timing doesn't reveal registered emails.
_DUMMY_HASH = _password_hash.hash("timing-attack-mitigation")


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if password_hash is None:
        _password_hash.verify(password, _DUMMY_HASH)
        return False
    return _password_hash.verify(password, password_hash)


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    subject: str
    email: str
    roles: tuple[str, ...]


def create_access_token(
    *, subject: str, email: str, roles: list[str], settings: Settings
) -> tuple[str, int]:
    now = datetime.now(UTC)
    expires_in = settings.access_token_ttl_minutes * 60
    payload: dict[str, Any] = {
        "iss": settings.jwt_issuer,
        "sub": subject,
        "email": email,
        "realm_access": {"roles": roles},
        "typ": "access",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(
        payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm
    )
    return token, expires_in


def decode_access_token(token: str, settings: Settings) -> AccessTokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "sub", "iss"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Срок действия токена истёк") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Недействительный токен") from exc

    if payload.get("typ") != "access":
        raise AuthenticationError("Недействительный токен")

    roles = payload.get("realm_access", {}).get("roles", [])
    return AccessTokenClaims(
        subject=str(payload["sub"]),
        email=str(payload.get("email", "")),
        roles=tuple(str(role) for role in roles),
    )


@dataclass(frozen=True, slots=True)
class RefreshTokenClaims:
    subject: str
    token_id: uuid.UUID


def create_refresh_token(
    *, subject: str, token_id: uuid.UUID, settings: Settings
) -> tuple[str, int]:
    now = datetime.now(UTC)
    expires_in = settings.refresh_token_ttl_days * 24 * 60 * 60
    payload: dict[str, Any] = {
        "iss": settings.jwt_issuer,
        "sub": subject,
        "jti": str(token_id),
        "typ": "refresh",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(
        payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm
    )
    return token, expires_in


def decode_refresh_token(token: str, settings: Settings) -> RefreshTokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "sub", "iss", "jti"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Срок действия сессии истёк") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Сессия недействительна") from exc

    if payload.get("typ") != "refresh":
        raise AuthenticationError("Сессия недействительна")
    try:
        token_id = uuid.UUID(str(payload["jti"]))
    except ValueError as exc:
        raise AuthenticationError("Сессия недействительна") from exc
    return RefreshTokenClaims(subject=str(payload["sub"]), token_id=token_id)
