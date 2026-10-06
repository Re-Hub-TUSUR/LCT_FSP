import uuid

import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("s3cret-value")
    assert hashed != "s3cret-value"
    assert verify_password("s3cret-value", hashed)
    assert not verify_password("other", hashed)
    assert not verify_password("anything", None)


def test_token_roundtrip_uses_keycloak_like_claims() -> None:
    settings = get_settings()
    token, expires_in = create_access_token(
        subject="user-1", email="a@b.ru", roles=["employer"], settings=settings
    )
    claims = decode_access_token(token, settings)
    assert expires_in == settings.access_token_ttl_minutes * 60
    assert claims.subject == "user-1"
    assert claims.roles == ("employer",)


def test_refresh_token_is_not_an_access_token() -> None:
    settings = get_settings()
    token_id = uuid.uuid4()
    refresh, _ = create_refresh_token(subject="user-1", token_id=token_id, settings=settings)
    claims = decode_refresh_token(refresh, settings)
    assert claims.token_id == token_id
    with pytest.raises(AuthenticationError):
        decode_access_token(refresh, settings)


def test_token_signed_with_other_secret_is_rejected() -> None:
    settings = get_settings()
    other = settings.model_copy(update={"jwt_secret": SecretStr("x" * 40)})
    token, _ = create_access_token(subject="u", email="a@b.ru", roles=[], settings=other)
    with pytest.raises(AuthenticationError):
        decode_access_token(token, settings)


def test_short_jwt_secret_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="sqlite+aiosqlite://", jwt_secret="short")


def test_cors_origins_are_parsed_from_comma_list() -> None:
    settings = Settings(
        database_url="sqlite+aiosqlite://",
        jwt_secret="y" * 40,
        cors_origins="http://a.test, http://b.test",
    )
    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_cors_wildcard_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="sqlite+aiosqlite://",
            jwt_secret="y" * 40,
            cors_origins="*",
        )
