"""The nginx gate opens the existing administrator session. A client header is not enough."""

from httpx import AsyncClient
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.security import hash_password
from app.dependencies.common import get_settings as settings_dependency
from app.models import User, UserRole
from tests.conftest import API, PASSWORD, create_admin

EMAIL = "admin@kadry.test"
SECRET = "test-admin-gate-secret"
HEADER = {"X-Admin-Gate": SECRET}


async def test_admin_gate_opens_the_administrator_session(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    await create_admin(sessionmaker, EMAIL)

    response = await client.post(f"{API}/auth/admin-gate", headers=HEADER)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user"]["email"] == EMAIL
    assert body["user"]["role"] == "admin"
    assert body["accessToken"]
    assert "kadry_refresh" in response.headers["set-cookie"]


async def test_admin_gate_rejects_a_missing_or_wrong_secret(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    await create_admin(sessionmaker, EMAIL)

    missing = await client.post(f"{API}/auth/admin-gate")
    wrong = await client.post(f"{API}/auth/admin-gate", headers={"X-Admin-Gate": "not-the-secret"})

    assert missing.status_code == 401
    assert wrong.status_code == 401


async def test_admin_gate_rejects_a_non_admin_account(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    async with sessionmaker() as session:
        session.add(
            User(
                email=EMAIL,
                password_hash=hash_password(PASSWORD),
                role=UserRole.CANDIDATE,
                is_email_verified=True,
            )
        )
        await session.commit()

    response = await client.post(f"{API}/auth/admin-gate", headers=HEADER)

    assert response.status_code == 401


async def test_admin_gate_stays_closed_without_a_secret(client: AsyncClient) -> None:
    app = client._transport.app  # type: ignore[attr-defined]
    closed = get_settings().model_copy(update={"admin_gate_secret": SecretStr("")})
    app.dependency_overrides[settings_dependency] = lambda: closed

    response = await client.post(f"{API}/auth/admin-gate", headers=HEADER)

    assert response.status_code == 404
