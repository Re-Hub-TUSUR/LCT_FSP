from httpx import AsyncClient

from tests.conftest import API


async def test_liveness(client: AsyncClient) -> None:
    response = await client.get(f"{API}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


async def test_readiness_checks_database(client: AsyncClient) -> None:
    response = await client.get(f"{API}/health/ready")
    assert response.status_code == 200
