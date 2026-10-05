from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.conftest import API, bearer, create_admin, login, register_and_login


async def test_protected_endpoint_requires_token(client: AsyncClient) -> None:
    response = await client.get(f"{API}/users/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


async def test_invalid_token_rejected(client: AsyncClient) -> None:
    response = await client.get(f"{API}/users/me", headers=bearer("not-a-jwt"))
    assert response.status_code == 401


async def test_admin_endpoint_forbidden_for_candidate(client: AsyncClient) -> None:
    token = await register_and_login(client, "cand@fsp.ru")
    response = await client.get(f"{API}/admin/users", headers=bearer(token))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


async def test_admin_lists_users(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    await register_and_login(client, "cand@fsp.ru")
    await create_admin(sessionmaker, "admin@fsp.ru")
    token = await login(client, "admin@fsp.ru")

    response = await client.get(f"{API}/admin/users?page=1&perPage=10", headers=bearer(token))

    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["page"], body["perPage"], body["pages"]) == (2, 1, 10, 1)
    assert {user["email"] for user in body["items"]} == {"cand@fsp.ru", "admin@fsp.ru"}


async def test_admin_pagination_splits_into_pages(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    await register_and_login(client, "one@fsp.ru")
    await register_and_login(client, "two@fsp.ru")
    await create_admin(sessionmaker, "admin@fsp.ru")
    token = await login(client, "admin@fsp.ru")

    second = await client.get(f"{API}/admin/users?page=2&perPage=2", headers=bearer(token))
    beyond = await client.get(f"{API}/admin/users?page=3&perPage=2", headers=bearer(token))
    invalid = await client.get(f"{API}/admin/users?page=0", headers=bearer(token))

    assert second.json()["pages"] == 2
    assert len(second.json()["items"]) == 1
    assert beyond.json()["items"] == []
    assert invalid.status_code == 422


async def test_role_guard_runs_before_stub(client: AsyncClient) -> None:
    """Employer-only contract must reject candidates even while it is not implemented."""
    token = await register_and_login(client, "cand2@fsp.ru")
    response = await client.get(f"{API}/matching/recommendations", headers=bearer(token))
    assert response.status_code == 403
