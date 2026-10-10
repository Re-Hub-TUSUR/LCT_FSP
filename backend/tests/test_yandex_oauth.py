"""Yandex ID sign-in. The directory is scripted: these tests never call Yandex."""

from urllib.parse import parse_qs, urlparse

import httpx
from httpx import AsyncClient
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.admin.models import AdminBanEntry
from app.core.config import get_settings
from app.core.security import verify_password
from app.dependencies.services import get_yandex_directory
from app.integrations.yandex.client import HttpYandexDirectory, YandexAccount
from app.models import User
from tests.conftest import API, PASSWORD, bearer, register_and_login

REDIRECT = "http://localhost:8080/auth/yandex/callback"
JPEG = b"\xff\xd8\xff" + b"\x00" * 8
RESUME = {
    "displayName": "Анна Смирнова",
    "headline": "Backend-разработчик",
    "specialization": "backend",
    "city": "Казань",
    "experienceYears": 4,
    "workFormats": ["hybrid"],
    "employmentTypes": ["full"],
    "stack": ["Python", "PostgreSQL", "Docker"],
    "phone": "+7 900 000-00-00",
}


class ScriptedYandex:
    def __init__(self, account: YandexAccount) -> None:
        self.account = account

    async def fetch(self, *, code: str, redirect_uri: str) -> YandexAccount:
        assert code == "ok"
        assert redirect_uri == REDIRECT
        return self.account


def _account(**overrides: object) -> YandexAccount:
    values: dict[str, object] = {
        "account_id": "ya-1",
        "email": "Anna@Yandex.ru",
        "first_name": "Анна",
        "last_name": "Смирнова",
        "portrait": (JPEG, "image/jpeg"),
    }
    values.update(overrides)
    return YandexAccount(**values)  # type: ignore[arg-type]


async def _install(client: AsyncClient, account: YandexAccount) -> ScriptedYandex:
    app = client._transport.app  # type: ignore[attr-defined]
    directory = ScriptedYandex(account)
    opened = get_settings().model_copy(
        update={
            "yandex_client_id": "test-client",
            "yandex_client_secret": SecretStr("test-secret"),
        }
    )
    app.dependency_overrides[get_settings] = lambda: opened
    app.dependency_overrides[get_yandex_directory] = lambda: directory
    return directory


async def _start(
    client: AsyncClient,
    *,
    mode: str,
    role: str = "candidate",
    consent: bool = False,
    redirect_uri: str = REDIRECT,
) -> httpx.Response:
    return await client.post(
        f"{API}/auth/yandex/start",
        json={
            "role": role,
            "mode": mode,
            "personalDataConsent": consent,
            "redirectUri": redirect_uri,
        },
    )


def _state(response: httpx.Response) -> str:
    url: str = response.json()["authorizeUrl"]
    return parse_qs(urlparse(url).query)["state"][0]


async def _finish(client: AsyncClient, state: str) -> httpx.Response:
    return await client.post(f"{API}/auth/yandex/callback", json={"code": "ok", "state": state})


async def test_yandex_stays_closed_without_a_client_id(client: AsyncClient) -> None:
    status = await client.get(f"{API}/auth/yandex")
    started = await _start(client, mode="sign-in")
    assert status.status_code == started.status_code == 404


async def test_sign_up_requires_consent(client: AsyncClient) -> None:
    await _install(client, _account())
    response = await _start(client, mode="sign-up", consent=False)
    assert response.status_code == 400
    assert "согласие" in response.json()["error"]["message"]


async def test_sign_up_creates_a_verified_account_and_stages_the_portrait(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    await _install(client, _account())
    started = await _start(client, mode="sign-up", consent=True)
    assert started.status_code == 200, started.text
    scope = parse_qs(urlparse(started.json()["authorizeUrl"]).query)["scope"][0]
    assert scope == "login:info login:email login:avatar"

    done = await _finish(client, _state(started))
    assert done.status_code == 200, done.text
    body = done.json()
    assert body["created"] is True
    assert body["user"]["email"] == "anna@yandex.ru"
    assert body["user"]["firstName"] == "Анна"
    assert body["user"]["lastName"] == "Смирнова"
    assert body["user"]["isEmailVerified"] is True
    assert "kadry_refresh" in done.headers["set-cookie"]

    token = body["accessToken"]
    pending = await client.get(f"{API}/users/me/pending-photo", headers=bearer(token))
    assert pending.status_code == 200
    assert pending.content == JPEG

    saved = await client.patch(f"{API}/candidates/me", headers=bearer(token), json=RESUME)
    assert saved.status_code == 200, saved.text
    assert saved.json()["hasPhoto"] is True
    assert saved.json()["displayName"] == "Анна Смирнова"

    gone = await client.get(f"{API}/users/me/pending-photo", headers=bearer(token))
    photo = await client.get(f"{API}/candidates/me/photo", headers=bearer(token))
    assert gone.status_code == 404
    assert photo.content == JPEG

    denied = await client.post(
        f"{API}/auth/login", json={"email": "anna@yandex.ru", "password": PASSWORD}
    )
    assert denied.status_code == 401

    async with sessionmaker() as session:
        user = await session.scalar(select(User).where(User.email == "anna@yandex.ru"))
        assert user is not None
        assert user.yandex_id == "ya-1"
        assert user.personal_data_consent is True
        assert user.pending_photo_type is None
        assert verify_password(PASSWORD, user.password_hash) is False


async def test_employer_sign_up_keeps_the_name_without_a_portrait(client: AsyncClient) -> None:
    await _install(client, _account(account_id="ya-boss", email="boss@yandex.ru"))
    started = await _start(client, mode="sign-up", role="employer", consent=True)
    done = await _finish(client, _state(started))
    assert done.status_code == 200, done.text
    assert done.json()["user"]["role"] == "employer"
    assert done.json()["user"]["firstName"] == "Анна"
    assert done.json()["user"]["lastName"] == "Смирнова"
    pending = await client.get(
        f"{API}/users/me/pending-photo", headers=bearer(done.json()["accessToken"])
    )
    assert pending.status_code == 404


async def test_known_yandex_id_opens_a_session(client: AsyncClient) -> None:
    await _install(client, _account())
    first = await _finish(client, _state(await _start(client, mode="sign-up", consent=True)))
    assert first.json()["created"] is True

    again = await _finish(client, _state(await _start(client, mode="sign-in")))
    assert again.status_code == 200, again.text
    assert again.json()["created"] is False
    assert again.json()["user"]["email"] == "anna@yandex.ru"


async def test_sign_in_does_not_create_an_account(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    await _install(client, _account())
    response = await _finish(client, _state(await _start(client, mode="sign-in")))
    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Сначала зарегистрируйтесь"
    async with sessionmaker() as session:
        count = await session.scalar(select(func.count()).select_from(User))
        assert count == 0


async def test_same_role_email_links_yandex_id(client: AsyncClient) -> None:
    await register_and_login(client, "anna@yandex.ru")
    await _install(client, _account(portrait=None))
    response = await _finish(client, _state(await _start(client, mode="sign-in")))
    assert response.status_code == 200, response.text
    assert response.json()["created"] is False
    assert response.json()["user"]["firstName"] == "Анна"


async def test_other_role_is_refused(client: AsyncClient) -> None:
    await register_and_login(client, "anna@yandex.ru", role="employer")
    await _install(client, _account())
    response = await _finish(client, _state(await _start(client, mode="sign-up", consent=True)))
    assert response.status_code == 409
    assert "другой ролью" in response.json()["error"]["message"]


async def test_banned_email_is_refused(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    async with sessionmaker() as session:
        session.add(AdminBanEntry(email="anna@yandex.ru", reason="спам", is_active=True))
        await session.commit()
    await _install(client, _account())
    response = await _finish(client, _state(await _start(client, mode="sign-up", consent=True)))
    assert response.status_code == 403


async def test_bad_state_and_foreign_redirect_are_refused(client: AsyncClient) -> None:
    await _install(client, _account())
    forged = await client.post(
        f"{API}/auth/yandex/callback", json={"code": "ok", "state": "not-a-token"}
    )
    foreign = await _start(
        client, mode="sign-in", redirect_uri="https://evil.example/auth/yandex/callback"
    )
    assert forged.status_code == 401
    assert foreign.status_code == 400


async def test_directory_skips_the_placeholder_and_keeps_a_real_portrait() -> None:
    settings = get_settings().model_copy(
        update={"yandex_client_id": "id", "yandex_client_secret": SecretStr("secret")}
    )

    def empty(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "tok"})
        return httpx.Response(
            200,
            json={
                "id": "42",
                "default_email": "a@yandex.ru",
                "first_name": "Анна",
                "last_name": "Смирнова",
                "is_avatar_empty": True,
                "default_avatar_id": "0/0-0",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(empty)) as http:
        account = await HttpYandexDirectory(settings, client=http).fetch(
            code="ok", redirect_uri=REDIRECT
        )
    assert account.portrait is None
    assert account.account_id == "42"

    def portrait(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "tok"})
        if request.url.host == "avatars.yandex.net":
            return httpx.Response(200, content=JPEG)
        return httpx.Response(
            200,
            json={
                "id": "42",
                "default_email": "a@yandex.ru",
                "first_name": "Анна",
                "last_name": "Смирнова",
                "is_avatar_empty": False,
                "default_avatar_id": "61207/enc-1",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(portrait)) as http:
        account = await HttpYandexDirectory(settings, client=http).fetch(
            code="ok", redirect_uri=REDIRECT
        )
    assert account.portrait == (JPEG, "image/jpeg")
