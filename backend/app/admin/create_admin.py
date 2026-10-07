"""`uv run python -m app.admin.create_admin`: create the administrator account from the env.

ADMIN_EMAIL and ADMIN_PASSWORD (at least 12 characters) come from the environment or the shared
`.env`, never from the command line, so the password does not end up in the shell history.
Running it again sets the new password of the same admin; an existing non-admin account is
never promoted.
"""

import asyncio
import sys
from typing import Final

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import get_engine, get_sessionmaker
from app.models import User, UserRole

EMAIL_ENV: Final = "ADMIN_EMAIL"
PASSWORD_ENV: Final = "ADMIN_PASSWORD"  # noqa: S105 - variable name, not a secret
MIN_PASSWORD: Final = 12


class AdminSetupError(Exception):
    pass


class _AdminEnv(BaseSettings):
    """Read like the app settings: real env vars first, then the shared .env files."""

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    admin_email: str = ""
    admin_password: SecretStr = SecretStr("")


async def ensure_admin(session: AsyncSession, email: str, password: str) -> bool:
    """True when the account was created, False when its password was updated."""
    email = email.strip().lower()
    if "@" not in email:
        raise AdminSetupError(f"{EMAIL_ENV} is not an email")
    if len(password) < MIN_PASSWORD:
        raise AdminSetupError(f"{PASSWORD_ENV} must be at least {MIN_PASSWORD} characters")
    user = await session.scalar(select(User).where(User.email == email))
    if user is not None and user.role != UserRole.ADMIN:
        raise AdminSetupError(f"{email} belongs to a {user.role.value} account; use another email")
    created = user is None
    if user is None:
        user = User(email=email, role=UserRole.ADMIN, personal_data_consent=True)
        session.add(user)
    user.password_hash = hash_password(password)
    user.is_email_verified = True
    user.is_active = True
    await session.flush()
    return created


async def _run(email: str, password: str) -> bool:
    try:
        async with get_sessionmaker()() as session:
            created = await ensure_admin(session, email, password)
            await session.commit()
            return created
    finally:
        await get_engine().dispose()


def main() -> int:
    env = _AdminEnv()
    email = env.admin_email
    password = env.admin_password.get_secret_value()
    if not email or not password:
        print(f"Set {EMAIL_ENV} and {PASSWORD_ENV} in the environment or .env", file=sys.stderr)
        return 1
    try:
        created = asyncio.run(_run(email, password))
    except AdminSetupError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Admin {'created' if created else 'password updated'}: {email.strip().lower()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
