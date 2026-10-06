from httpx import AsyncClient

from tests.conftest import API, PASSWORD, bearer, login, register_and_login


async def test_register_login_and_read_me(client: AsyncClient) -> None:
    token = await register_and_login(client, "Dev@FSP.ru", role="employer")

    response = await client.get(f"{API}/users/me", headers=bearer(token))

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "dev@fsp.ru"
    assert body["role"] == "employer"
    assert body["isEmailVerified"] is True
    assert "passwordHash" not in body


async def test_login_response_contains_user(client: AsyncClient) -> None:
    await register_and_login(client, "a@fsp.ru")
    response = await client.post(
        f"{API}/auth/login", json={"email": "a@fsp.ru", "password": PASSWORD}
    )
    body = response.json()
    assert body["tokenType"] == "bearer"
    assert body["expiresIn"] > 0
    assert body["user"]["role"] == "candidate"


async def test_duplicate_email_conflicts(client: AsyncClient) -> None:
    await register_and_login(client, "dup@fsp.ru")
    response = await client.post(
        f"{API}/auth/register",
        json={
            "email": "DUP@fsp.ru",
            "password": PASSWORD,
            "role": "candidate",
            "personalDataConsent": True,
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


async def test_wrong_password_and_unknown_email_look_the_same(client: AsyncClient) -> None:
    await register_and_login(client, "b@fsp.ru")
    wrong = await client.post(f"{API}/auth/login", json={"email": "b@fsp.ru", "password": "nope"})
    unknown = await client.post(
        f"{API}/auth/login", json={"email": "ghost@fsp.ru", "password": "nope"}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert wrong.headers["WWW-Authenticate"] == "Bearer"


async def test_registration_requires_consent_and_forbids_admin_role(client: AsyncClient) -> None:
    no_consent = await client.post(
        f"{API}/auth/register",
        json={"email": "c@fsp.ru", "password": PASSWORD, "role": "candidate"},
    )
    as_admin = await client.post(
        f"{API}/auth/register",
        json={
            "email": "d@fsp.ru",
            "password": PASSWORD,
            "role": "admin",
            "personalDataConsent": True,
        },
    )
    assert no_consent.status_code == as_admin.status_code == 422
    assert no_consent.json()["error"]["code"] == "validation_error"


async def test_short_password_rejected(client: AsyncClient) -> None:
    response = await client.post(
        f"{API}/auth/register",
        json={
            "email": "e@fsp.ru",
            "password": "short",
            "role": "candidate",
            "personalDataConsent": True,
        },
    )
    assert response.status_code == 422


async def test_relogin_returns_fresh_token(client: AsyncClient) -> None:
    await register_and_login(client, "f@fsp.ru")
    assert await login(client, "f@fsp.ru")


CSRF = {"X-Kadry-Request": "1"}


async def test_refresh_cookie_restores_the_session_and_logout_revokes_it(
    client: AsyncClient,
) -> None:
    await register_and_login(client, "keep@fsp.ru")
    forged = await client.post(f"{API}/auth/refresh")
    assert forged.status_code == 401

    refreshed = await client.post(f"{API}/auth/refresh", headers=CSRF)
    assert refreshed.status_code == 200, refreshed.text
    cookie = refreshed.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    token = refreshed.json()["accessToken"]
    me = await client.get(f"{API}/users/me", headers=bearer(token))
    assert me.status_code == 200
    assert me.json()["email"] == "keep@fsp.ru"

    blocked = await client.post(f"{API}/auth/logout")
    assert blocked.status_code == 401
    logged_out = await client.post(f"{API}/auth/logout", headers=CSRF)
    assert logged_out.status_code == 204
    again = await client.post(f"{API}/auth/refresh", headers=CSRF)
    assert again.status_code == 401


async def test_api_responses_cannot_be_sniffed_or_framed(client: AsyncClient) -> None:
    response = await client.get(f"{API}/health")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
