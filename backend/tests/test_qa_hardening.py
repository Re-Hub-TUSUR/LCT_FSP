"""Regressions for the QA run and the security audit of October 2026."""

import asyncio
import io
import json
import uuid
import zipfile
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient
from PIL import Image
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.requests import Request

from app.admin.csv_export import render
from app.admin.enums import VerificationStatus
from app.admin.models import CompanyVerification
from app.core.config import get_settings
from app.core.http_body import read_json
from app.dependencies.auth import through_admin_gate
from app.models import AssessmentAttempt, CandidateCategory, CandidateProfile, Grade
from app.models.enums import AttemptStatus
from app.services.assessments import _failed_by
from app.services.notifications import MAX_STREAMS_PER_USER, NotificationHub, TooManyStreamsError
from app.services.uploads import MAX_IMAGE_PIXELS, is_docx, sniff_chat_attachment, sniff_image
from tests.conftest import (
    API,
    PASSWORD,
    bearer,
    create_admin,
    login,
    make_inn,
    register_and_login,
)
from tests.test_cabinet import COMPANY, RESUME, employer_with_company
from tests.test_invitations import OFFER
from tests.test_yandex_oauth import _account, _finish, _install, _start, _state

# ── Grade and visibility of a profile ──────────────────────────────────────────────────────


async def test_a_grade_stays_with_its_specialization(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    token = await register_and_login(client, "grade-move@fsp.ru")
    saved = await client.patch(f"{API}/candidates/me", headers=bearer(token), json=RESUME)
    profile_id = uuid.UUID(saved.json()["id"])
    now = datetime.now(UTC)
    async with sessionmaker() as session:
        session.add(
            CandidateCategory(
                candidate_id=profile_id,
                specialization="backend",
                grade=Grade.SENIOR,
                score=91.0,
                confirmed_at=now,
                change_allowed_at=now,
            )
        )
        profile = await session.get(CandidateProfile, profile_id)
        assert profile is not None
        profile.grade = Grade.SENIOR
        profile.assessment_score = 91.0
        await session.commit()

    moved = await client.patch(
        f"{API}/candidates/me", headers=bearer(token), json={"specialization": "devops"}
    )
    assert moved.status_code == 200, moved.text
    assert moved.json()["category"] is None
    assert moved.json()["gradeVerified"] is False
    assert moved.json()["assessmentStatus"] == "not_taken"

    back = await client.patch(
        f"{API}/candidates/me", headers=bearer(token), json={"specialization": "backend"}
    )
    assert back.json()["category"]["grade"] == "senior"
    assert back.json()["assessmentScore"] == 91.0


async def test_a_profile_is_shown_only_with_the_consent(client: AsyncClient) -> None:
    token = await register_and_login(client, "no-consent@fsp.ru")
    without = {key: value for key, value in RESUME.items() if key != "profileDisplayConsent"}
    saved = await client.patch(f"{API}/candidates/me", headers=bearer(token), json=without)
    assert saved.json()["searching"] is False

    agreed = await client.patch(
        f"{API}/candidates/me", headers=bearer(token), json={"profileDisplayConsent": True}
    )
    assert agreed.json()["searching"] is True
    withdrawn = await client.patch(
        f"{API}/candidates/me", headers=bearer(token), json={"profileDisplayConsent": False}
    )
    assert withdrawn.json()["searching"] is False


async def test_salaries_have_an_upper_bound(client: AsyncClient) -> None:
    token = await register_and_login(client, "rich@fsp.ru")
    response = await client.patch(
        f"{API}/candidates/me",
        headers=bearer(token),
        json={**RESUME, "salaryExpectation": 2_000_000_000},
    )
    assert response.status_code == 422


# ── Employers ──────────────────────────────────────────────────────────────────────────────


async def test_the_candidate_bank_needs_a_company_profile(client: AsyncClient) -> None:
    anyone = await register_and_login(client, "anyone@fsp.ru", role="employer")
    response = await client.get(f"{API}/candidates", headers=bearer(anyone))
    assert response.status_code == 409


async def test_a_block_signs_the_owner_out_and_a_restriction_limits_invitations(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    await create_admin(sessionmaker, "mod@fsp.ru")
    admin = bearer(await login(client, "mod@fsp.ru"))
    owner = await employer_with_company(client, "limited@fsp.ru")
    company_id = (await client.get(f"{API}/companies/me", headers=bearer(owner))).json()["id"]
    first = await register_and_login(client, "cand-a@fsp.ru")
    second = await register_and_login(client, "cand-b@fsp.ru")
    ids = []
    for token in (first, second):
        saved = await client.patch(f"{API}/candidates/me", headers=bearer(token), json=RESUME)
        ids.append(saved.json()["id"])

    restricted = await client.post(
        f"{API}/admin/employers/{company_id}/decision",
        headers=admin,
        json={"action": "restrict", "reason": "Массовые приглашения", "inviteLimit": 1},
    )
    assert restricted.status_code == 200, restricted.text
    sent = await client.post(
        f"{API}/invitations", headers=bearer(owner), json={**OFFER, "candidateId": ids[0]}
    )
    over = await client.post(
        f"{API}/invitations", headers=bearer(owner), json={**OFFER, "candidateId": ids[1]}
    )
    assert sent.status_code == 201, sent.text
    assert over.status_code == 429

    blocked = await client.post(
        f"{API}/admin/employers/{company_id}/decision",
        headers=admin,
        json={"action": "block", "reason": "Фиктивная компания"},
    )
    assert blocked.status_code == 200
    banned = await client.get(f"{API}/companies/me", headers=bearer(owner))
    assert banned.status_code == 403
    assert banned.json()["error"]["code"] == "account_banned"
    relogin = await client.post(
        f"{API}/auth/login", json={"email": "limited@fsp.ru", "password": PASSWORD}
    )
    assert relogin.status_code == 403
    assert relogin.json()["error"]["details"]["reason"] == "Фиктивная компания"

    await client.post(
        f"{API}/admin/employers/{company_id}/decision",
        headers=admin,
        json={"action": "clear", "reason": "Проверили документы"},
    )
    # The case can be closed. The ban row is what keeps the account out until it is lifted.
    still = await client.post(
        f"{API}/auth/login", json={"email": "limited@fsp.ru", "password": PASSWORD}
    )
    assert still.status_code == 403
    ban_id = (await client.get(f"{API}/admin/banlist?q=limited", headers=admin)).json()["items"][0][
        "id"
    ]
    lifted = await client.post(
        f"{API}/admin/banlist/{ban_id}/unban", headers=admin, json={"reason": "Ошибка"}
    )
    assert lifted.status_code == 200, lifted.text
    assert await login(client, "limited@fsp.ru")


async def test_new_legal_details_reopen_the_accreditation(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    owner = await employer_with_company(client, "accredited@fsp.ru")
    mine = (await client.get(f"{API}/companies/me", headers=bearer(owner))).json()
    async with sessionmaker() as session:
        session.add(
            CompanyVerification(
                company_id=uuid.UUID(mine["id"]),
                status=VerificationStatus.APPROVED,
                submitted_at=datetime.now(UTC),
                decided_at=datetime.now(UTC),
            )
        )
        await session.commit()
    assert (await client.get(f"{API}/companies/me", headers=bearer(owner))).json()["itAccredited"]

    payload = {**COMPANY, "inn": make_inn("another-company")}
    changed = await client.put(f"{API}/companies/me", headers=bearer(owner), json=payload)
    assert changed.status_code == 200, changed.text
    assert changed.json()["itAccredited"] is False
    async with sessionmaker() as session:
        check = await session.get(CompanyVerification, uuid.UUID(mine["id"]))
        assert check is not None
        assert check.status == VerificationStatus.PENDING


# ── Sign-in ────────────────────────────────────────────────────────────────────────────────


async def test_yandex_callback_must_come_from_the_browser_that_started_it(
    client: AsyncClient,
) -> None:
    await _install(client, _account())
    started = await _start(client, mode="sign-up", consent=True)
    client.cookies.clear()
    stolen = await _finish(client, _state(started))
    assert stolen.status_code == 401


async def test_yandex_takes_over_an_unverified_account_without_its_password(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    squatter = await client.post(
        f"{API}/auth/register",
        json={
            "email": "anna@yandex.ru",
            "password": PASSWORD,
            "role": "candidate",
            "personalDataConsent": True,
        },
    )
    assert squatter.status_code == 201
    await _install(client, _account())
    done = await _finish(client, _state(await _start(client, mode="sign-in")))
    assert done.status_code == 200, done.text
    login_attempt = await client.post(
        f"{API}/auth/login", json={"email": "anna@yandex.ru", "password": PASSWORD}
    )
    assert login_attempt.status_code == 401


async def test_a_refresh_cookie_works_once(client: AsyncClient) -> None:
    await register_and_login(client, "once@fsp.ru")
    cookie = client.cookies.get("kadry_refresh")
    csrf = {"X-Kadry-Request": "1"}
    first = await client.post(f"{API}/auth/refresh", headers=csrf)
    assert first.status_code == 200
    client.cookies.set("kadry_refresh", cookie or "", path="/api/v1/auth")
    replay = await client.post(f"{API}/auth/refresh", headers=csrf)
    assert replay.status_code == 401


def _request(headers: dict[str, str]) -> Request:
    raw = [(key.lower().encode(), value.encode()) for key, value in headers.items()]
    return Request({"type": "http", "headers": raw})


def test_the_admin_api_needs_the_gate_in_production() -> None:
    settings = get_settings().model_copy(
        update={"app_env": "production", "admin_gate_secret": SecretStr("gate-secret-123456")}
    )
    assert through_admin_gate(_request({}), settings) is False
    assert through_admin_gate(_request({"X-Admin-Gate": "wrong"}), settings) is False
    assert through_admin_gate(_request({"X-Admin-Gate": "gate-secret-123456"}), settings)
    assert through_admin_gate(_request({}), get_settings())


# ── Files and external data ────────────────────────────────────────────────────────────────


def _zip(*names: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name in names:
            archive.writestr(name, "<x/>")
    return buffer.getvalue()


def test_only_a_word_document_passes_as_docx() -> None:
    assert is_docx(_zip("[Content_Types].xml", "word/document.xml"))
    assert not is_docx(_zip("[Content_Types].xml", "ppt/presentation.xml"))
    assert not is_docx(_zip("word/document.xml", "word/vbaProject.bin"))
    assert sniff_chat_attachment(_zip("ppt/presentation.xml")) is None


def test_an_image_header_promising_too_many_pixels_is_refused() -> None:
    small = io.BytesIO()
    Image.new("RGB", (8, 8)).save(small, format="PNG")
    assert sniff_image(small.getvalue()) == "image/png"
    assert sniff_image(b"\x89PNG\r\n\x1a\n" + bytes(32)) is None
    side = int(MAX_IMAGE_PIXELS**0.5) + 100
    huge = io.BytesIO()
    Image.new("1", (side, side)).save(huge, format="PNG")
    assert sniff_image(huge.getvalue()) is None


def test_csv_cells_never_become_formulas() -> None:
    text = render(["a", "b", "c"], [["=HYPERLINK(1)", "@cmd", 42], ["-1+2", "+x", "ok"]])
    assert "'=HYPERLINK(1)" in text
    assert "'@cmd" in text
    assert "'-1+2" in text
    assert "'+x" in text
    assert ";42" in text


async def test_a_forged_request_id_is_replaced(client: AsyncClient) -> None:
    forged = await client.get(f"{API}/health", headers={"X-Request-ID": "x\r\nFAKE LOG LINE"})
    kept = await client.get(f"{API}/health", headers={"X-Request-ID": "proxy-42.a_b"})
    assert "FAKE" not in forged.headers["x-request-id"]
    assert kept.headers["x-request-id"] == "proxy-42.a_b"


def test_an_oversized_upstream_answer_is_not_read_whole() -> None:
    small = read_json(io.BytesIO(b'{"ok": true}'))
    assert small == {"ok": True}
    with pytest.raises(json.JSONDecodeError):
        read_json(io.BytesIO(b"[" + b"1," * 100 + b"1]"), limit=50)


async def test_notification_streams_per_account_are_capped() -> None:
    hub = NotificationHub()
    user = uuid.uuid4()
    queues = [hub.subscribe(user) for _ in range(MAX_STREAMS_PER_USER)]
    with pytest.raises(TooManyStreamsError):
        hub.subscribe(user)
    hub.unsubscribe(user, queues[0])
    hub.subscribe(user)
    await asyncio.sleep(0)


# ── Tests ──────────────────────────────────────────────────────────────────────────────────


def _attempt(**values: Any) -> AssessmentAttempt:
    return AssessmentAttempt(**{"pass_score": 60, "quiz_min": 0, "interview": None, **values})


def test_a_failed_attempt_names_its_reason() -> None:
    assert _failed_by(_attempt(status=AttemptStatus.FAILED, score=40.0), None) == "score"
    interview = _attempt(status=AttemptStatus.FAILED, score=100.0, interview={"questions": []})
    assert _failed_by(interview, None) == "interview"
    quiz = _attempt(status=AttemptStatus.FAILED, score=80.0, quiz_min=70)
    assert _failed_by(quiz, 50.0) == "quiz"
    assert _failed_by(_attempt(status=AttemptStatus.PASSED, score=90.0), None) is None
