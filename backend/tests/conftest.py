import os

# Must be set before `app` modules read settings. Real env vars take precedence over .env files.
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-only-secret-that-is-long-enough-123456"
os.environ["CORS_ORIGINS"] = ""
# A key in a developer's .env must never make the tests call the paid model.
os.environ["ROUTERAI_API_KEY"] = ""
os.environ["ATS_POLL_SECONDS"] = "0"
os.environ["ADMIN_EMAIL"] = "admin@kadry.test"
os.environ["ADMIN_GATE_SECRET"] = "test-admin-gate-secret"

import io
import zlib
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.dependencies.common import get_db_session
from app.main import create_app
from app.models import User, UserRole

API = "/api/v1"
PASSWORD = "correct-horse-battery"


@pytest.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    yield engine
    await engine.dispose()


@pytest.fixture
async def sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def client(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncClient]:
    async def override_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[get_db_session] = override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http


async def register_and_login(client: AsyncClient, email: str, role: str = "candidate") -> str:
    response = await client.post(
        f"{API}/auth/register",
        json={"email": email, "password": PASSWORD, "role": role, "personalDataConsent": True},
    )
    assert response.status_code == 201, response.text
    verified = await client.post(
        f"{API}/auth/verify-email", json={"email": email, "code": "000000"}
    )
    assert verified.status_code == 204, verified.text
    return await login(client, email)


async def login(client: AsyncClient, email: str) -> str:
    response = await client.post(f"{API}/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return str(response.json()["accessToken"])


async def create_admin(sessionmaker: async_sessionmaker[AsyncSession], email: str) -> None:
    async with sessionmaker() as session:
        session.add(
            User(
                email=email,
                password_hash=hash_password(PASSWORD),
                role=UserRole.ADMIN,
                is_email_verified=True,
            )
        )
        await session.commit()


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def tiny_image(fmt: str = "PNG") -> bytes:
    """A real picture: uploads read its header, so magic bytes alone are not a photo."""
    buffer = io.BytesIO()
    Image.new("RGB", (4, 3), (64, 47, 255)).save(buffer, format=fmt)
    return buffer.getvalue()


def make_inn(seed: str) -> str:
    """A valid 10-digit organisation INN, different for different seeds."""
    digits = [int(char) for char in f"77{zlib.crc32(seed.encode()) % 10**7:07d}"]
    weights = (2, 4, 10, 3, 5, 9, 4, 6, 8)
    check = sum(d * w for d, w in zip(digits, weights, strict=True)) % 11 % 10
    return "".join(map(str, digits)) + str(check)
