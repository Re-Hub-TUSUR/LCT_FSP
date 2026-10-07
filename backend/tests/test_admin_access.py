"""Every admin panel endpoint is closed to anyone but an admin."""

import pytest
from fastapi.routing import APIRoute
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.admin.routes import panel_router
from tests.conftest import API, bearer, create_admin, login, register_and_login

TASK = "00000000-0000-0000-0000-000000000001"
COMPANY = "00000000-0000-0000-0000-000000000002"

ADMIN_ENDPOINTS = [
    ("GET", "/admin/bank/tasks"),
    ("GET", "/admin/bank/tasks/export.csv"),
    ("GET", "/admin/bank/skills"),
    ("POST", "/admin/bank/preview"),
    ("POST", "/admin/bank/tasks"),
    ("GET", f"/admin/bank/tasks/{TASK}"),
    ("PUT", f"/admin/bank/tasks/{TASK}"),
    ("POST", f"/admin/bank/tasks/{TASK}/status"),
    ("DELETE", f"/admin/bank/tasks/{TASK}"),
    ("GET", f"/admin/bank/tasks/{TASK}/history"),
    ("GET", "/admin/analytics/tasks"),
    ("GET", "/admin/analytics/employers"),
    ("GET", "/admin/analytics/snapshot/tasks"),
    ("POST", "/admin/analytics/tasks/recalculate"),
    ("POST", "/admin/analytics/platform/recalculate"),
    ("GET", "/admin/analytics/tasks/export.csv?table=tasks"),
    ("GET", f"/admin/employers/{COMPANY}"),
    ("POST", f"/admin/employers/{COMPANY}/decision"),
    ("GET", "/admin/banlist"),
    ("POST", "/admin/banlist"),
    ("GET", "/admin/banlist/export.csv"),
    ("POST", f"/admin/banlist/{TASK}/unban"),
    ("GET", f"/admin/banlist/{TASK}/history"),
    ("GET", "/admin/dictionaries"),
    ("POST", "/admin/dictionaries/specializations"),
    ("PATCH", "/admin/dictionaries/specializations/backend"),
    ("POST", "/admin/dictionaries/skills"),
    ("PATCH", f"/admin/dictionaries/skills/{TASK}"),
    ("GET", "/admin/parameters"),
    ("PUT", "/admin/parameters/p_pass"),
    ("GET", "/admin/audit"),
    ("GET", "/admin/audit/export.csv"),
    ("GET", "/admin/users/export.csv"),
    ("GET", "/admin/verifications"),
    ("GET", "/admin/verifications/pending-count"),
    ("GET", "/admin/verifications/export.csv"),
    ("GET", f"/admin/verifications/{COMPANY}"),
    ("GET", f"/admin/verifications/{COMPANY}/documents/{TASK}"),
    ("POST", f"/admin/verifications/{COMPANY}/approve"),
    ("POST", f"/admin/verifications/{COMPANY}/reject"),
]


def test_every_panel_route_is_listed() -> None:
    """A new admin route must be added to the access check above."""
    values = {
        "{task_id}": TASK,
        "{ban_id}": TASK,
        "{document_id}": TASK,
        "{skill_id}": TASK,
        "{company_id}": COMPANY,
        "{code}": "backend",
        "{key}": "p_pass",
        "{block}": "tasks",
    }

    def concrete(path: str) -> str:
        for name, value in values.items():
            path = path.replace(name, value)
        return f"/admin{path}"

    routes = {
        (method, concrete(route.path))
        for route in panel_router.routes
        if isinstance(route, APIRoute)
        for method in route.methods or ()
    }
    listed = {(method, path.split("?")[0]) for method, path in ADMIN_ENDPOINTS}
    assert routes - listed == set(), "admin routes without an access test"


@pytest.mark.parametrize(("method", "path"), ADMIN_ENDPOINTS)
async def test_anonymous_gets_401(client: AsyncClient, method: str, path: str) -> None:
    response = await client.request(method, f"{API}{path}", json={})
    assert response.status_code == 401, response.text


async def test_candidate_and_employer_get_403(client: AsyncClient) -> None:
    tokens = [
        await register_and_login(client, "cand@fsp.ru"),
        await register_and_login(client, "boss@fsp.ru", role="employer"),
    ]
    for token in tokens:
        for method, path in ADMIN_ENDPOINTS:
            response = await client.request(method, f"{API}{path}", headers=bearer(token), json={})
            assert response.status_code == 403, f"{method} {path}: {response.text}"
            assert response.json()["error"]["code"] == "forbidden"


async def test_admin_passes_the_guard(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    await create_admin(sessionmaker, "admin@fsp.ru")
    token = await login(client, "admin@fsp.ru")
    for path in ("/admin/bank/tasks", "/admin/dictionaries", "/admin/parameters", "/admin/banlist"):
        response = await client.get(f"{API}{path}", headers=bearer(token))
        assert response.status_code == 200, f"{path}: {response.text}"


async def test_company_documents_are_for_employers(client: AsyncClient) -> None:
    anonymous = await client.get(f"{API}/companies/me/verification")
    token = await register_and_login(client, "cand@fsp.ru")
    candidate = await client.get(f"{API}/companies/me/verification", headers=bearer(token))
    assert anonymous.status_code == 401
    assert candidate.status_code == 403
