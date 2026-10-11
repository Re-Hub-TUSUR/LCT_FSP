from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qsl, urlsplit

import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.security import hash_password
from app.integrations.fsp import mock, registry
from app.integrations.fsp.http import HttpCallError
from app.integrations.fsp.keycloak import KeycloakFspIdProvider
from app.integrations.fsp.provider import FspIdError, code_challenge
from app.integrations.fsp.registry import FspRegistryError, HttpFspRegistryClient
from app.integrations.fsp.schemas import FspMemberRecord
from app.integrations.fsp.sync import apply_record
from app.models import CandidateProfile
from app.seed.fixtures import load_seed_data
from app.seed.generate import DEMO_CANDIDATE_EMAIL
from app.seed.loader import seed_database
from tests.conftest import API, PASSWORD, bearer, login, register_and_login
from tests.test_cabinet import RESUME, employer_with_company

CALLBACK = "http://localhost:5173/profile/fsp/callback"
REALM = f"{API}/mock/fsp-id/realms/fsp"
MEMBER = "FSP-100101"


async def candidate(client: AsyncClient, email: str) -> str:
    token = await register_and_login(client, email)
    saved = await client.patch(f"{API}/candidates/me", headers=bearer(token), json=RESUME)
    assert saved.status_code == 200, saved.text
    return token


async def fsp_sign_in(client: AsyncClient, token: str, member_id: str) -> dict[str, str]:
    """Walks the browser part of the flow: our authorize URL, the realm's page, its redirect."""
    started = await client.post(
        f"{API}/fsp-id/authorize", headers=bearer(token), json={"redirectUri": CALLBACK}
    )
    assert started.status_code == 200, started.text
    url = urlsplit(started.json()["authorizeUrl"])
    assert url.path == f"{REALM}/protocol/openid-connect/auth"
    params = dict(parse_qsl(url.query))
    assert params["code_challenge_method"] == "S256"
    assert "openid" in params["scope"].split()

    page = await client.get(url.path, params=params)
    assert page.status_code == 200
    assert "Вход через ФСП ID" in page.text
    assert "form-action 'self' http://localhost:5173" in page.headers["content-security-policy"]

    hidden = {key: params[key] for key in ("client_id", "redirect_uri", "state", "nonce")}
    confirmed = await client.get(
        f"{url.path}/confirm",
        params={**hidden, "code_challenge": params["code_challenge"], "member": member_id},
    )
    assert confirmed.status_code == 302, confirmed.text
    back = urlsplit(confirmed.headers["location"])
    assert f"{back.scheme}://{back.netloc}{back.path}" == CALLBACK
    query = dict(parse_qsl(back.query))
    assert query["state"] == params["state"]
    return {"code": query["code"], "state": query["state"]}


async def link(client: AsyncClient, token: str, member_id: str) -> Any:
    answer = await fsp_sign_in(client, token, member_id)
    return await client.post(f"{API}/candidates/me/fsp-link", headers=bearer(token), json=answer)


async def test_linking_imports_the_registry_history(client: AsyncClient) -> None:
    token = await candidate(client, "fsp-link@fsp.ru")
    linked = await link(client, token, MEMBER)
    assert linked.status_code == 200, linked.text
    body = linked.json()
    record = mock.member_record(MEMBER)
    assert body["fspLinked"] is True
    assert body["fspMemberId"] == MEMBER
    assert body["fspLinkedAt"] is not None
    assert body["fspSyncedAt"] is not None
    assert body["fspSyncError"] is None
    assert len(body["fspAchievements"]) == len(record.achievements) > 0
    assert len(body["fspTitles"]) == len(record.titles)
    first = body["fspAchievements"][0]
    assert {"eventKind", "result", "participation", "teamName"} <= first.keys()

    employer = await employer_with_company(client, "fsp-hr@fsp.ru")
    seen = await client.get(f"{API}/candidates/{body['id']}", headers=bearer(employer))
    assert len(seen.json()["fspAchievements"]) == len(record.achievements)
    assert "fspSyncError" not in seen.json()

    again = await client.post(f"{API}/candidates/me/fsp-sync", headers=bearer(token))
    assert again.status_code == 200
    assert again.json()["fspAchievements"] == body["fspAchievements"]
    assert again.json()["fspLinkedAt"] == body["fspLinkedAt"]


async def test_one_participant_links_to_one_account(client: AsyncClient) -> None:
    first = await candidate(client, "fsp-first@fsp.ru")
    assert (await link(client, first, MEMBER)).status_code == 200

    second = await candidate(client, "fsp-second@fsp.ru")
    conflict = await link(client, second, MEMBER)
    assert conflict.status_code == 409
    assert "другим аккаунтом" in conflict.json()["error"]["message"]

    cleared = await client.delete(f"{API}/candidates/me/fsp-link", headers=bearer(first))
    assert cleared.status_code == 200
    assert cleared.json()["fspLinked"] is False
    assert cleared.json()["fspMemberId"] is None
    assert cleared.json()["fspAchievements"] == []
    assert cleared.json()["fspTitles"] == []
    assert cleared.json()["fspSyncedAt"] is None
    assert (await link(client, second, MEMBER)).status_code == 200


async def test_candidate_without_fsp_history_links_normally(client: AsyncClient) -> None:
    token = await candidate(client, "fsp-none@fsp.ru")
    linked = await link(client, token, mock.NO_HISTORY_ID)
    assert linked.status_code == 200
    assert linked.json()["fspLinked"] is True
    assert linked.json()["fspAchievements"] == []
    assert linked.json()["fspSyncedAt"] is not None
    assert linked.json()["fspSyncError"] is None


async def test_registry_failure_keeps_the_link(client: AsyncClient) -> None:
    token = await candidate(client, "fsp-down@fsp.ru")
    linked = await link(client, token, mock.REGISTRY_DOWN_ID)
    assert linked.status_code == 200
    assert linked.json()["fspLinked"] is True
    assert linked.json()["fspSyncError"] == "Реестр ФСП временно недоступен"
    assert linked.json()["fspSyncedAt"] is None

    retried = await client.post(f"{API}/candidates/me/fsp-sync", headers=bearer(token))
    assert retried.status_code == 200
    assert retried.json()["fspMemberId"] == mock.REGISTRY_DOWN_ID
    assert retried.json()["fspSyncError"] is not None


async def test_relinking_another_participant_replaces_the_history(client: AsyncClient) -> None:
    token = await candidate(client, "fsp-switch@fsp.ru")
    assert (await link(client, token, MEMBER)).status_code == 200
    switched = await link(client, token, "FSP-200777")
    assert switched.status_code == 200
    expected = mock.generated_member("FSP-200777")
    names = {item["eventName"] for item in switched.json()["fspAchievements"]}
    assert names == {item.event_name for item in expected.achievements}
    assert len(switched.json()["fspAchievements"]) == len(expected.achievements)


async def test_a_flow_started_by_another_account_is_refused(client: AsyncClient) -> None:
    alice = await candidate(client, "fsp-alice@fsp.ru")
    mallory = await candidate(client, "fsp-mallory@fsp.ru")
    alice_answer = await fsp_sign_in(client, alice, MEMBER)
    mallory_answer = await fsp_sign_in(client, mallory, MEMBER)

    stolen_state = await client.post(
        f"{API}/candidates/me/fsp-link", headers=bearer(mallory), json=alice_answer
    )
    assert stolen_state.status_code == 400
    assert stolen_state.json()["error"]["code"] == "fsp_id_failed"

    # Alice's code with Mallory's own state fails PKCE: the verifier is bound to the account.
    stolen_code = await client.post(
        f"{API}/candidates/me/fsp-link",
        headers=bearer(mallory),
        json={"code": alice_answer["code"], "state": mallory_answer["state"]},
    )
    assert stolen_code.status_code == 400
    assert "PKCE" in stolen_code.json()["error"]["message"]


async def test_authorize_rejects_foreign_redirects_and_unsaved_resumes(
    client: AsyncClient,
) -> None:
    fresh = await register_and_login(client, "fsp-fresh@fsp.ru")
    missing = await client.post(
        f"{API}/fsp-id/authorize", headers=bearer(fresh), json={"redirectUri": CALLBACK}
    )
    assert missing.status_code == 404

    token = await candidate(client, "fsp-redirect@fsp.ru")
    foreign = await client.post(
        f"{API}/fsp-id/authorize",
        headers=bearer(token),
        json={"redirectUri": "https://evil.example/profile/fsp/callback"},
    )
    assert foreign.status_code == 400

    not_linked = await client.post(f"{API}/candidates/me/fsp-sync", headers=bearer(token))
    assert not_linked.status_code == 400

    employer = await register_and_login(client, "fsp-hr2@fsp.ru", role="employer")
    forbidden = await client.post(
        f"{API}/fsp-id/authorize", headers=bearer(employer), json={"redirectUri": CALLBACK}
    )
    assert forbidden.status_code == 403


async def test_user_can_deny_access_on_the_realm_page(client: AsyncClient) -> None:
    settings = get_settings()
    denied = await client.get(
        f"{REALM}/protocol/openid-connect/auth/confirm",
        params={
            "client_id": settings.fsp_id_client_id,
            "redirect_uri": CALLBACK,
            "state": "s",
            "nonce": "n",
            "code_challenge": "c",
            "action": "deny",
        },
    )
    assert denied.status_code == 302
    assert "error=access_denied" in denied.headers["location"]

    unknown = await client.get(
        f"{REALM}/protocol/openid-connect/auth",
        params={
            "client_id": settings.fsp_id_client_id,
            "redirect_uri": "https://evil.example/cb",
            "state": "s",
            "nonce": "n",
            "code_challenge": "c",
        },
    )
    assert unknown.status_code == 400


async def test_mock_realm_speaks_keycloak_token_and_userinfo(client: AsyncClient) -> None:
    settings = get_settings()
    discovery = await client.get(f"{REALM}/.well-known/openid-configuration")
    assert discovery.json()["token_endpoint"].endswith("/protocol/openid-connect/token")

    verifier = "v" * 48
    code = mock.issue_code(
        settings,
        member_id=MEMBER,
        client_id=settings.fsp_id_client_id,
        redirect_uri=CALLBACK,
        code_challenge=code_challenge(verifier),
        nonce="n-1",
    )
    form = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": CALLBACK,
        "client_id": settings.fsp_id_client_id,
    }
    wrong = await client.post(
        f"{REALM}/protocol/openid-connect/token", data={**form, "code_verifier": "x" * 48}
    )
    assert wrong.status_code == 400
    assert wrong.json()["error"] == "invalid_grant"

    tokens = await client.post(
        f"{REALM}/protocol/openid-connect/token", data={**form, "code_verifier": verifier}
    )
    assert tokens.status_code == 200, tokens.text
    claims = jwt.decode(tokens.json()["id_token"], options={"verify_signature": False})
    assert claims["fsp_member_id"] == MEMBER
    assert claims["nonce"] == "n-1"

    info = await client.get(
        f"{REALM}/protocol/openid-connect/userinfo",
        headers=bearer(tokens.json()["access_token"]),
    )
    assert info.json()["fsp_member_id"] == MEMBER
    # An ID token is not an access token.
    refused = await client.get(
        f"{REALM}/protocol/openid-connect/userinfo", headers=bearer(tokens.json()["id_token"])
    )
    assert refused.status_code == 401

    member = await client.get(f"{API}/mock/fsp-registry/members/{MEMBER}")
    assert member.json()["memberId"] == MEMBER
    down = await client.get(f"{API}/mock/fsp-registry/members/{mock.REGISTRY_DOWN_ID}")
    assert down.status_code == 503


async def test_resync_of_a_demo_account_changes_nothing(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    async with sessionmaker() as session:
        await seed_database(session, load_seed_data(), password_hash=hash_password(PASSWORD))
        await session.commit()

    token = await login(client, DEMO_CANDIDATE_EMAIL)
    before = await client.get(f"{API}/candidates/me", headers=bearer(token))
    after = await client.post(f"{API}/candidates/me/fsp-sync", headers=bearer(token))
    assert after.status_code == 200
    assert after.json()["fspAchievements"] == before.json()["fspAchievements"]
    assert after.json()["fspTitles"] == before.json()["fspTitles"]


def test_apply_record_upserts_by_external_id() -> None:
    record = mock.generated_member("FSP-300300")
    profile = CandidateProfile(fsp_achievements=[], fsp_titles=[])
    apply_record(profile, record)
    assert [item.external_id for item in profile.fsp_achievements] == [
        item.id for item in record.achievements
    ]
    kept = profile.fsp_achievements[0]

    shorter = FspMemberRecord(member_id=record.member_id, achievements=record.achievements[:1])
    apply_record(profile, shorter)
    assert profile.fsp_achievements == [kept]
    assert profile.fsp_titles == []
    assert profile.fsp_synced_at is not None
    assert profile.fsp_sync_error is None


def test_generated_history_is_stable() -> None:
    assert mock.generated_member("FSP-424242") == mock.generated_member("FSP-424242")
    assert mock.member_record(mock.NO_HISTORY_ID).achievements == []
    with pytest.raises(FspRegistryError):
        mock.member_record(mock.REGISTRY_DOWN_ID)


async def test_http_registry_client(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings().model_copy(update={"fsp_registry_url": "https://registry.example"})
    record = mock.generated_member("FSP-555555")
    answers: dict[str, Any] = {"body": record.model_dump(mode="json", by_alias=True)}
    calls: list[str] = []

    async def post_form(url: str, form: dict[str, str]) -> dict[str, Any]:
        assert form["grant_type"] == "client_credentials"
        return {"access_token": "service"}

    async def get_json(url: str, *, bearer: str) -> Any:
        calls.append(url)
        assert bearer == "service"
        if isinstance(answers["body"], HttpCallError):
            raise answers["body"]
        return answers["body"]

    monkeypatch.setattr(registry, "post_form", post_form)
    monkeypatch.setattr(registry, "get_json", get_json)
    client = HttpFspRegistryClient(settings)

    assert await client.fetch_member("FSP-555555") == record
    assert calls == ["https://registry.example/members/FSP-555555"]

    with pytest.raises(FspRegistryError, match="другого участника"):
        await client.fetch_member("FSP-666666")

    answers["body"] = HttpCallError("not found", status=404)
    assert (await client.fetch_member("FSP-777777")).achievements == []

    answers["body"] = HttpCallError("boom", status=500)
    with pytest.raises(FspRegistryError):
        await client.fetch_member("FSP-777777")

    unconfigured = HttpFspRegistryClient(get_settings())
    with pytest.raises(FspRegistryError, match="не настроен"):
        await unconfigured.fetch_member("FSP-777777")


async def test_keycloak_provider_checks_the_id_token(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings().model_copy(
        update={"fsp_id_mode": "keycloak", "fsp_id_issuer": "https://id.fsp.example/realms/fsp"}
    )
    now = datetime.now(UTC)
    claims = {
        "iss": "https://id.fsp.example/realms/fsp",
        "aud": [settings.fsp_id_client_id, "account"],
        "sub": "kc-user",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "nonce": "n-2",
        "fsp_member_id": "FSP-900900",
    }
    sent: list[dict[str, str]] = []

    async def post_form(url: str, form: dict[str, str]) -> dict[str, Any]:
        assert url == "https://id.fsp.example/realms/fsp/protocol/openid-connect/token"
        sent.append(form)
        return {"id_token": jwt.encode(claims, "realm-key-we-do-not-know-xxxxxxxxxxxxxx")}

    monkeypatch.setattr("app.integrations.fsp.keycloak.post_form", post_form)
    provider = KeycloakFspIdProvider(settings)
    exchange = {"code": "c", "code_verifier": "v", "redirect_uri": CALLBACK}

    identity = await provider.exchange_code(**exchange, nonce="n-2")
    assert identity.member_id == "FSP-900900"
    assert sent[0]["code_verifier"] == "v"
    assert sent[0]["grant_type"] == "authorization_code"

    with pytest.raises(FspIdError):
        await provider.exchange_code(**exchange, nonce="other")

    claims["iss"] = "https://evil.example/realms/fsp"
    with pytest.raises(FspIdError):
        await provider.exchange_code(**exchange, nonce="n-2")


async def test_mock_realm_accepts_local_origins_and_offers_a_random_participant(
    client: AsyncClient,
) -> None:
    """A demo opened through Docker (:8080) or by a LAN address links without configuration."""
    token = await candidate(client, "fsp-local@fsp.ru")

    async def started(redirect_uri: str) -> int:
        response = await client.post(
            f"{API}/fsp-id/authorize", headers=bearer(token), json={"redirectUri": redirect_uri}
        )
        return response.status_code

    assert await started("http://localhost:8080/profile/fsp/callback") == 200
    assert await started("http://127.0.0.1:8080/profile/fsp/callback") == 200
    assert await started("http://192.168.1.20:5173/profile/fsp/callback") == 200
    assert await started("http://localhost:8080/elsewhere") == 400
    assert await started("https://8.8.8.8/profile/fsp/callback") == 400

    first, second = mock.random_member_id(), mock.random_member_id()
    assert first != second
    assert first not in mock.DEMO_MEMBERS
    linked = await link(client, token, first)
    assert linked.status_code == 200, linked.text
    body = linked.json()
    assert (body["fspLinked"], body["fspMemberId"], body["fspSyncError"]) == (True, first, None)
    assert len(body["fspAchievements"]) > 0


async def test_mock_keycloak_signs_in_with_a_demo_password(client: AsyncClient) -> None:
    token = await candidate(client, "fsp-login@fsp.ru")
    started = await client.post(
        f"{API}/fsp-id/authorize", headers=bearer(token), json={"redirectUri": CALLBACK}
    )
    assert started.status_code == 200, started.text
    url = urlsplit(started.json()["authorizeUrl"])
    params = dict(parse_qsl(url.query))
    page = await client.get(url.path, params=params)
    assert page.status_code == 200
    assert mock.DEMO_PASSWORD in page.text
    assert "champion" in page.text
    confirm = "/api/v1/mock/fsp-id/realms/fsp/protocol/openid-connect/auth/confirm"
    assert f'action="{confirm}"' in page.text
    hidden = {
        key: params[key]
        for key in ("client_id", "redirect_uri", "state", "nonce", "code_challenge")
    }

    wrong = await client.post(
        f"{url.path}/confirm",
        data={**hidden, "login": "champion", "password": "not-the-password", "action": "allow"},
    )
    assert wrong.status_code == 401
    assert "Неверный логин или пароль" in wrong.text

    signed_in = await client.post(
        f"{url.path}/confirm",
        data={**hidden, "login": "Champion", "password": mock.DEMO_PASSWORD, "action": "allow"},
    )
    assert signed_in.status_code == 302, signed_in.text
    query = dict(parse_qsl(urlsplit(signed_in.headers["location"]).query))
    linked = await client.post(
        f"{API}/candidates/me/fsp-link",
        headers=bearer(token),
        json={"code": query["code"], "state": query["state"]},
    )
    assert linked.status_code == 200, linked.text
    assert linked.json()["fspMemberId"] == "FSP-100101"
