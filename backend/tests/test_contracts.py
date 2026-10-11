from httpx import AsyncClient

from tests.conftest import API, bearer, register_and_login

EXPECTED_TAGS = {
    "health",
    "auth",
    "users",
    "categories",
    "candidates",
    "cities",
    "companies",
    "vacancies",
    "invitations",
    "applications",
    "matching",
    "calendar",
    "responses",
    "conversations",
    "notifications",
    "assessments",
    "admin",
    "ats",
    "fsp-id",
    # The emulated FSP ID realm and registry, present only with FSP_ID_MODE=mock.
    "mock-fsp",
}


async def test_openapi_documents_all_domains(client: AsyncClient) -> None:
    response = await client.get("/api/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    tags = {tag for path in spec["paths"].values() for op in path.values() for tag in op["tags"]}
    assert tags == EXPECTED_TAGS
    assert "ErrorResponse" in spec["components"]["schemas"]


async def test_not_implemented_contract_uses_error_envelope(client: AsyncClient) -> None:
    token = await register_and_login(client, "stub@fsp.ru", role="employer")
    response = await client.get(f"{API}/matching/recommendations", headers=bearer(token))
    assert response.status_code == 501
    error = response.json()["error"]
    assert error["code"] == "not_implemented"
    assert error["details"] == {"operation": "matching.recommendations"}


async def test_invitation_requires_ordered_salary_range(client: AsyncClient) -> None:
    token = await register_and_login(client, "hr@fsp.ru", role="employer")
    response = await client.post(
        f"{API}/invitations",
        headers=bearer(token),
        json={
            "candidateId": "00000000-0000-0000-0000-000000000001",
            "message": "Предлагаем позицию backend-разработчика в команде платежей",
            "salary": {"from": 300000, "to": 200000},
            "contactMethod": "@hr",
        },
    )
    assert response.status_code == 422


async def test_category_dictionary(client: AsyncClient) -> None:
    response = await client.get(f"{API}/categories/dictionary")
    assert response.status_code == 200
    body = response.json()
    assert {"code": "backend", "label": "Backend-разработка"} in body["specializations"]
    assert body["grades"][0]["code"] == "intern"


async def test_unknown_route_uses_error_envelope(client: AsyncClient) -> None:
    response = await client.get(f"{API}/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_404"
