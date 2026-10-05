from httpx import AsyncClient

from tests.conftest import API, PASSWORD


async def test_login_before_verification_asks_for_the_code(client: AsyncClient) -> None:
    registered = await client.post(
        f"{API}/auth/register",
        json={
            "email": "new@fsp.ru",
            "password": PASSWORD,
            "role": "candidate",
            "personalDataConsent": True,
        },
    )
    assert registered.status_code == 201
    assert registered.json()["isEmailVerified"] is False

    login = await client.post(
        f"{API}/auth/login", json={"email": "new@fsp.ru", "password": PASSWORD}
    )
    assert login.status_code == 403
    assert login.json()["error"]["code"] == "email_not_verified"


async def test_wrong_code_is_rejected_and_the_right_one_lets_you_in(client: AsyncClient) -> None:
    await client.post(
        f"{API}/auth/register",
        json={
            "email": "code@fsp.ru",
            "password": PASSWORD,
            "role": "candidate",
            "personalDataConsent": True,
        },
    )
    wrong = await client.post(
        f"{API}/auth/verify-email", json={"email": "code@fsp.ru", "code": "111111"}
    )
    assert wrong.status_code == 401

    verified = await client.post(
        f"{API}/auth/verify-email", json={"email": "code@fsp.ru", "code": "000000"}
    )
    assert verified.status_code == 204

    login = await client.post(
        f"{API}/auth/login", json={"email": "code@fsp.ru", "password": PASSWORD}
    )
    assert login.status_code == 200
    assert login.json()["user"]["isEmailVerified"] is True


async def test_resend_is_silent_for_unknown_email_and_limited_for_a_real_one(
    client: AsyncClient,
) -> None:
    unknown = await client.post(f"{API}/auth/resend-verification", json={"email": "nobody@fsp.ru"})
    assert unknown.status_code == 204

    await client.post(
        f"{API}/auth/register",
        json={
            "email": "again@fsp.ru",
            "password": PASSWORD,
            "role": "employer",
            "personalDataConsent": True,
        },
    )
    again = await client.post(f"{API}/auth/resend-verification", json={"email": "again@fsp.ru"})
    assert again.status_code == 429
    assert again.json()["error"]["code"] == "too_many_requests"
