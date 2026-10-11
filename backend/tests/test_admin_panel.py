"""Workflows of the admin panel: bank statuses, journal, parameters, dictionaries, moderation,
banlist and the company document check."""

import io
import json
import uuid
import zipfile
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.admin.activity import ActivityRecorder
from app.admin.create_admin import AdminSetupError, ensure_admin
from app.admin.dependencies import get_verification
from app.admin.services.verification import VerificationService, clean_filename, sniff_document
from app.core.config import get_settings
from app.dependencies.common import SessionDep
from app.dependencies.services import NotificationHubDep, get_chat_service
from app.models import AssessmentAttempt, AssessmentTask, CandidateProfile, User, UserRole
from app.repositories.candidate import CandidateRepository
from app.repositories.company import CompanyRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.meeting import MeetingRepository
from app.repositories.reaction import ReactionRepository
from app.repositories.vacancy import VacancyRepository
from app.services.chat import ChatService
from app.services.notifications import NotificationHub
from tests.conftest import API, PASSWORD, bearer, create_admin, login, make_inn, register_and_login
from tests.test_invitations import candidate_with_resume
from tests.test_vacancies import VACANCY

PDF = b"%PDF-1.7\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
COMPANY = {
    "name": "ООО Проверка",
    "industry": "Финтех",
    "description": "Компания для проверки документов. " * 4,
    "city": "Москва",
    "website": "https://example.ru",
    "contactEmail": "hr@example.ru",
}


def quiz(title: str = "Сумма", **extra: Any) -> dict[str, Any]:
    return {
        "kind": "quiz",
        "title": title,
        "statement": "Сколько будет {a} + {b}?",
        "specializations": ["backend"],
        "grade": "middle-minus",
        "skill": "arithmetic",
        "variables": [{"name": "a", "min": 1, "max": 9}, {"name": "b", "min": 10, "max": 20}],
        "timeLimitMinutes": 5,
        "payload": {"options": ["{a}{b}", "другое"], "correct": [0]},
        **extra,
    }


@pytest.fixture
async def admin(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> dict[str, str]:
    await create_admin(sessionmaker, "admin@fsp.ru")
    return bearer(await login(client, "admin@fsp.ru"))


@pytest.fixture
async def uploads(client: AsyncClient, tmp_path: Path) -> AsyncIterator[Path]:
    """Documents go to a temporary folder instead of UPLOAD_DIR."""
    settings = get_settings().model_copy(update={"upload_dir": str(tmp_path)})

    def service(session: SessionDep, hub: NotificationHubDep) -> VerificationService:
        return VerificationService(session, settings, hub)

    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_verification] = service
    yield tmp_path
    app.dependency_overrides.pop(get_verification)


async def employer_with_company(client: AsyncClient, email: str = "boss@fsp.ru") -> dict[str, str]:
    headers = bearer(await register_and_login(client, email, role="employer"))
    saved = await client.put(
        f"{API}/companies/me", headers=headers, json={**COMPANY, "inn": make_inn(email)}
    )
    assert saved.status_code == 200, saved.text
    return headers


# ── Task bank ───────────────────────────────────────────────────────────────────────────────────


async def test_bank_status_workflow_drives_delivery(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], admin: dict[str, str]
) -> None:
    created = await client.post(f"{API}/admin/bank/tasks", headers=admin, json=quiz())
    assert created.status_code == 201, created.text
    task = created.json()
    assert task["status"] == "draft"
    assert task["grade"] == "middle-minus"
    assert task["canDelete"] is True
    assert task["allowedStatuses"] == ["active", "archived"]

    async def delivered() -> bool:
        async with sessionmaker() as session:
            row = await session.get(AssessmentTask, uuid.UUID(task["id"]))
            assert row is not None
            return row.is_active

    assert await delivered() is False
    active = await client.post(
        f"{API}/admin/bank/tasks/{task['id']}/status", headers=admin, json={"status": "active"}
    )
    assert active.json()["status"] == "active"
    assert await delivered() is True

    leaked = await client.post(
        f"{API}/admin/bank/tasks/{task['id']}/status",
        headers=admin,
        json={"status": "leaked", "reason": "Разбор задания нашли в Telegram"},
    )
    assert leaked.json()["status"] == "leaked"
    assert await delivered() is False
    back = await client.post(
        f"{API}/admin/bank/tasks/{task['id']}/status", headers=admin, json={"status": "active"}
    )
    assert back.status_code == 409

    deleted = await client.delete(f"{API}/admin/bank/tasks/{task['id']}", headers=admin)
    assert deleted.status_code == 409

    history = await client.get(f"{API}/admin/bank/tasks/{task['id']}/history", headers=admin)
    entries = history.json()["items"]
    assert [entry["action"] for entry in entries] == ["status", "status", "create"]
    assert entries[0]["changes"] == {"status": ["active", "leaked"]}
    assert entries[0]["reason"] == "Разбор задания нашли в Telegram"
    assert entries[0]["actorEmail"] == "admin@fsp.ru"


async def test_bank_edit_is_journaled_and_filters_work(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    task = (await client.post(f"{API}/admin/bank/tasks", headers=admin, json=quiz())).json()
    await client.post(
        f"{API}/admin/bank/tasks",
        headers=admin,
        json=quiz(
            "Код",
            kind="code",
            skill="io",
            grade="senior",
            payload={
                "groups": [
                    {"input": "1", "expected": "1", "hidden": False},
                    {"input": "2", "expected": "2", "hidden": True},
                ]
            },
            status="active",
        ),
    )
    edited = await client.put(
        f"{API}/admin/bank/tasks/{task['id']}",
        headers=admin,
        json=quiz("Сумма двух чисел", grade="middle"),
    )
    assert edited.status_code == 200, edited.text
    history = (
        await client.get(f"{API}/admin/bank/tasks/{task['id']}/history", headers=admin)
    ).json()
    assert history["items"][0]["changes"] == {
        "grade": ["middle-minus", "middle"],
        "title": ["Сумма", "Сумма двух чисел"],
    }

    async def titles(query: str) -> list[str]:
        page = await client.get(f"{API}/admin/bank/tasks?{query}", headers=admin)
        assert page.status_code == 200, page.text
        return [item["title"] for item in page.json()["items"]]

    assert await titles("kind=code") == ["Код"]
    assert await titles("status=draft") == ["Сумма двух чисел"]
    assert await titles("grade=senior") == ["Код"]
    assert await titles("skill=arithmetic") == ["Сумма двух чисел"]
    assert await titles("specialization=backend&q=двух") == ["Сумма двух чисел"]
    assert await titles("specialization=qa") == []

    exported = await client.get(f"{API}/admin/bank/tasks/export.csv?kind=code", headers=admin)
    lines = exported.content.decode("utf-8").splitlines()
    assert lines[0].startswith("\ufeffID;Название;Тип")
    assert len(lines) == 2

    unknown = await client.post(f"{API}/admin/bank/tasks", headers=admin, json=quiz(grade="guru"))
    open_kind = await client.post(f"{API}/admin/bank/tasks", headers=admin, json=quiz(kind="open"))
    bad_payload = await client.post(
        f"{API}/admin/bank/tasks", headers=admin, json=quiz(payload={"options": ["один"]})
    )
    assert unknown.status_code == 400
    assert open_kind.status_code == 422
    assert bad_payload.status_code == 400


async def test_draft_without_attempts_is_deleted(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], admin: dict[str, str]
) -> None:
    lonely = (await client.post(f"{API}/admin/bank/tasks", headers=admin, json=quiz())).json()
    used = (
        await client.post(f"{API}/admin/bank/tasks", headers=admin, json=quiz("Был в тесте"))
    ).json()
    candidate = await register_and_login(client, "cand@fsp.ru")
    await client.get(f"{API}/assessments/status", headers=bearer(candidate))
    async with sessionmaker() as session:
        profile = await session.scalar(select(CandidateProfile))
        if profile is None:
            user = await session.scalar(select(User).where(User.email == "cand@fsp.ru"))
            assert user is not None
            profile = CandidateProfile(user_id=user.id, display_name="cand")
            session.add(profile)
            await session.flush()
        now = datetime.now(UTC)
        session.add(
            AssessmentAttempt(
                candidate_id=profile.id,
                title="t",
                pass_score=60,
                quiz_weight=40,
                started_at=now,
                expires_at=now + timedelta(minutes=30),
                task_ids=[used["id"]],
            )
        )
        await session.commit()

    detail = await client.get(f"{API}/admin/bank/tasks/{used['id']}", headers=admin)
    assert detail.json()["attempts"] == 1
    assert detail.json()["canDelete"] is False
    refused = await client.delete(f"{API}/admin/bank/tasks/{used['id']}", headers=admin)
    removed = await client.delete(f"{API}/admin/bank/tasks/{lonely['id']}", headers=admin)
    assert refused.status_code == 409
    assert removed.status_code == 204
    gone = await client.get(f"{API}/admin/bank/tasks/{lonely['id']}", headers=admin)
    assert gone.status_code == 404
    journal = await client.get(
        f"{API}/admin/audit?entity=task&entityId={lonely['id']}", headers=admin
    )
    assert journal.json()["items"][0]["action"] == "delete"


async def test_preview_substitutes_variables(client: AsyncClient, admin: dict[str, str]) -> None:
    response = await client.post(
        f"{API}/admin/bank/preview",
        headers=admin,
        json={
            "statement": "Сколько будет {a} + {b}? {unknown}",
            "variables": [
                {"name": "a", "min": 1, "max": 3},
                {"name": "b", "min": 0.5, "max": 1.5, "step": 0.5},
            ],
            "options": ["{a}", "нет"],
        },
    )
    assert response.status_code == 200, response.text
    variants = response.json()
    assert len(variants) == 3
    for variant in variants:
        a, b = variant["values"]["a"], variant["values"]["b"]
        assert a in {1, 2, 3}
        assert b in {0.5, 1.0, 1.5}
        assert variant["statement"].startswith(f"Сколько будет {int(a)} + ")
        assert variant["statement"].endswith("{unknown}")
        assert variant["options"] == [str(int(a)), "нет"]


# ── Parameters and dictionaries ─────────────────────────────────────────────────────────────────


async def test_parameters_are_validated_and_journaled(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    initial = (await client.get(f"{API}/admin/parameters", headers=admin)).json()
    values = {item["key"]: item["value"] for item in initial["items"]}
    assert values["target_solve_min"] == 50
    assert values["min_attempts_for_flags"] == 30
    # Pass thresholds belong to the test templates, not to the parameters.
    assert "p_pass" not in values
    assert initial["hardcoded"]

    changed = await client.put(
        f"{API}/admin/parameters/target_solve_min", headers=admin, json={"value": 60}
    )
    out_of_order = await client.put(
        f"{API}/admin/parameters/target_solve_max", headers=admin, json={"value": 55}
    )
    out_of_range = await client.put(
        f"{API}/admin/parameters/target_solve_min", headers=admin, json={"value": 101}
    )
    unknown = await client.put(f"{API}/admin/parameters/nope", headers=admin, json={"value": 1})
    assert changed.status_code == 200
    assert {i["key"]: i["value"] for i in changed.json()["items"]}["target_solve_min"] == 60
    assert out_of_order.status_code == 400
    assert out_of_range.status_code == 400
    assert unknown.status_code == 404

    journal = (await client.get(f"{API}/admin/audit?entity=parameter", headers=admin)).json()
    assert journal["total"] == 1
    assert journal["items"][0]["changes"] == {"value": [50, 60]}


async def test_dictionaries(client: AsyncClient, admin: dict[str, str]) -> None:
    data = (await client.get(f"{API}/admin/dictionaries", headers=admin)).json()
    assert [grade["label"] for grade in data["grades"]] == [
        "Junior-",
        "Junior",
        "Junior+",
        "Middle-",
        "Middle",
        "Middle+",
        "Senior-",
        "Senior",
        "Senior+",
        "Lead",
        "Head",
    ]
    codes = {item["code"] for item in data["specializations"]}
    assert {"backend", "frontend", "qa"} <= codes

    added = await client.post(
        f"{API}/admin/dictionaries/specializations",
        headers=admin,
        json={"code": "data-ml", "label": "Data/ML"},
    )
    duplicate = await client.post(
        f"{API}/admin/dictionaries/specializations",
        headers=admin,
        json={"code": "data-ml", "label": "Ещё раз"},
    )
    assert added.status_code == 200
    assert duplicate.status_code == 409
    ml = next(s for s in added.json()["specializations"] if s["code"] == "data-ml")
    assert ml["inPlatform"] is False

    renamed = await client.patch(
        f"{API}/admin/dictionaries/specializations/data-ml",
        headers=admin,
        json={"label": "Data / ML", "isArchived": True},
    )
    ml = next(s for s in renamed.json()["specializations"] if s["code"] == "data-ml")
    assert (ml["label"], ml["isArchived"]) == ("Data / ML", True)

    skill = await client.post(
        f"{API}/admin/dictionaries/skills",
        headers=admin,
        json={"specializationCode": "data-ml", "name": "pandas"},
    )
    assert any(s["name"] == "pandas" for s in skill.json()["skills"])
    journal = (await client.get(f"{API}/admin/audit", headers=admin)).json()
    assert {entry["entity"] for entry in journal["items"]} == {"specialization", "skill"}


# ── Employers and banlist ───────────────────────────────────────────────────────────────────────


async def test_banlist_add_search_unban(client: AsyncClient, admin: dict[str, str]) -> None:
    added = await client.post(
        f"{API}/admin/banlist",
        headers=admin,
        json={"inn": "7707083893", "emailDomain": "@Spam.RU", "reason": "Массовая рассылка"},
    )
    assert added.status_code == 201, added.text
    ban = added.json()
    assert (ban["emailDomain"], ban["isActive"], ban["createdByEmail"]) == (
        "spam.ru",
        True,
        "admin@fsp.ru",
    )
    empty = await client.post(f"{API}/admin/banlist", headers=admin, json={"reason": "нет цели"})
    bad_inn = await client.post(
        f"{API}/admin/banlist", headers=admin, json={"inn": "123", "reason": "плохой ИНН"}
    )
    assert empty.status_code == 422
    assert bad_inn.status_code == 422

    found = await client.get(f"{API}/admin/banlist?q=spam", headers=admin)
    assert found.json()["total"] == 1

    no_reason = await client.post(f"{API}/admin/banlist/{ban['id']}/unban", headers=admin, json={})
    unbanned = await client.post(
        f"{API}/admin/banlist/{ban['id']}/unban", headers=admin, json={"reason": "Ошибка"}
    )
    twice = await client.post(
        f"{API}/admin/banlist/{ban['id']}/unban", headers=admin, json={"reason": "Ещё раз"}
    )
    assert no_reason.status_code == 422
    assert unbanned.json()["isActive"] is False
    assert unbanned.json()["unbanReason"] == "Ошибка"
    assert twice.status_code == 409
    active = await client.get(f"{API}/admin/banlist?active=true", headers=admin)
    assert active.json()["total"] == 0
    history = await client.get(f"{API}/admin/banlist/{ban['id']}/history", headers=admin)
    assert [entry["action"] for entry in history.json()] == ["unban", "ban"]


async def test_employer_decisions_and_block(client: AsyncClient, admin: dict[str, str]) -> None:
    employer = await employer_with_company(client, "boss2@fsp.ru")
    mine = await client.get(f"{API}/companies/me", headers=employer)
    company_id = mine.json()["id"]

    no_reason = await client.post(
        f"{API}/admin/employers/{company_id}/decision", headers=admin, json={"action": "warn"}
    )
    no_limit = await client.post(
        f"{API}/admin/employers/{company_id}/decision",
        headers=admin,
        json={"action": "restrict", "reason": "Подозрительная активность"},
    )
    restricted = await client.post(
        f"{API}/admin/employers/{company_id}/decision",
        headers=admin,
        json={"action": "restrict", "reason": "Подозрительная активность", "inviteLimit": 5},
    )
    assert no_reason.status_code == 422
    assert no_limit.status_code == 422
    assert restricted.status_code == 200, restricted.text
    assert restricted.json()["case"] == {
        "status": "restricted",
        "inviteLimit": 5,
        "updatedAt": restricted.json()["case"]["updatedAt"],
    }

    blocked = await client.post(
        f"{API}/admin/employers/{company_id}/decision",
        headers=admin,
        json={"action": "block", "reason": "Фиктивные вакансии"},
    )
    card = blocked.json()
    assert card["case"]["status"] == "blocked"
    assert card["banned"] is True
    assert [entry["action"] for entry in card["history"]] == ["block", "restrict"]
    bans = (await client.get(f"{API}/admin/banlist", headers=admin)).json()
    assert bans["items"][0]["companyId"] == company_id
    assert bans["items"][0]["email"] == "boss2@fsp.ru"


async def test_employer_signals_snapshot(client: AsyncClient, admin: dict[str, str]) -> None:
    await employer_with_company(client)
    computed = await client.post(
        f"{API}/admin/analytics/employers/recalculate", headers=admin, json={"period": "90d"}
    )
    assert computed.status_code == 200, computed.text
    result = computed.json()["result"]
    assert result["summary"]["flagged"] == 0
    assert result["unavailable"]
    page = await client.get(f"{API}/admin/analytics/employers?signal=any", headers=admin)
    assert page.json()["total"] == 0


async def test_platform_funnels(client: AsyncClient, admin: dict[str, str]) -> None:
    await register_and_login(client, "c1@fsp.ru")
    await register_and_login(client, "c2@fsp.ru")
    await employer_with_company(client)
    computed = await client.post(
        f"{API}/admin/analytics/platform/recalculate", headers=admin, json={"period": "7d"}
    )
    result = computed.json()["result"]
    candidates = {step["step"]: step["count"] for step in result["candidateFunnel"]}
    employers = {step["step"]: step["count"] for step in result["employerFunnel"]}
    assert candidates["registered"] == 2
    assert candidates["started_test"] == 0
    assert employers["registered"] == 1
    assert employers["hired"] is None
    assert result["candidateFunnel"][1]["fromStartShare"] == 0.0


# ── Company documents ───────────────────────────────────────────────────────────────────────────


async def test_company_verification_flow(
    client: AsyncClient, admin: dict[str, str], uploads: Path
) -> None:
    no_company = bearer(await register_and_login(client, "new@fsp.ru", role="employer"))
    early = await client.post(
        f"{API}/companies/me/verification/documents",
        headers=no_company,
        files={"file": ("egrul.pdf", PDF, "application/pdf")},
    )
    assert early.status_code == 404

    employer = await employer_with_company(client)
    nothing = await client.get(f"{API}/companies/me/verification", headers=employer)
    assert nothing.json() == {
        "status": None,
        "submittedAt": None,
        "decidedAt": None,
        "reason": None,
        "documents": [],
    }
    not_pdf = await client.post(
        f"{API}/companies/me/verification/documents",
        headers=employer,
        files={"file": ("photo.pdf", b"\x89PNG\r\n\x1a\n", "application/pdf")},
    )
    assert not_pdf.status_code == 400

    uploaded = await client.post(
        f"{API}/companies/me/verification/documents",
        headers=employer,
        files={"file": ("Выписка ЕГРЮЛ.pdf", PDF, "application/pdf")},
    )
    assert uploaded.status_code == 201, uploaded.text
    assert uploaded.json()["status"] == "pending"
    assert uploaded.json()["documents"][0]["filename"] == "Выписка ЕГРЮЛ.pdf"
    assert stored_pdfs(uploads) == 1

    assert (await client.get(f"{API}/admin/verifications/pending-count", headers=admin)).json() == 1
    queue = (await client.get(f"{API}/admin/verifications?status=pending", headers=admin)).json()
    request = queue["items"][0]
    assert (request["companyName"], request["documents"]) == ("ООО Проверка", 1)
    company_id = request["companyId"]
    owner = (await client.get(f"{API}/users/me", headers=employer)).json()["id"]
    hub: NotificationHub = client._transport.app.state.notifications  # type: ignore[attr-defined]
    events = hub.subscribe(uuid.UUID(owner))

    detail = (await client.get(f"{API}/admin/verifications/{company_id}", headers=admin)).json()
    document_id = detail["files"][0]["id"]
    pdf = await client.get(
        f"{API}/admin/verifications/{company_id}/documents/{document_id}", headers=admin
    )
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content == PDF
    stolen = await client.get(
        f"{API}/admin/verifications/{company_id}/documents/{document_id}", headers=employer
    )
    assert stolen.status_code == 403

    no_reason = await client.post(
        f"{API}/admin/verifications/{company_id}/reject", headers=admin, json={}
    )
    rejected = await client.post(
        f"{API}/admin/verifications/{company_id}/reject",
        headers=admin,
        json={"reason": "Выписка старше 30 дней"},
    )
    assert no_reason.status_code == 422
    assert rejected.json()["status"] == "rejected"
    assert json.loads(events.get_nowait()) == {
        "type": "company_verification",
        "status": "rejected",
        "reason": "Выписка старше 30 дней",
    }
    seen = (await client.get(f"{API}/companies/me/verification", headers=employer)).json()
    assert (seen["status"], seen["reason"]) == ("rejected", "Выписка старше 30 дней")

    again = await client.post(
        f"{API}/companies/me/verification/documents",
        headers=employer,
        files={"file": ("new.pdf", PDF, "application/pdf")},
    )
    assert again.json()["status"] == "pending"
    assert again.json()["reason"] is None

    approved = await client.post(
        f"{API}/admin/verifications/{company_id}/approve", headers=admin, json={}
    )
    assert approved.json()["status"] == "approved"
    assert approved.json()["decidedByEmail"] == "admin@fsp.ru"
    assert [entry["action"] for entry in approved.json()["history"]] == ["approve", "reject"]
    assert json.loads(events.get_nowait())["status"] == "approved"
    locked = await client.delete(
        f"{API}/companies/me/verification/documents/{document_id}", headers=employer
    )
    assert locked.status_code == 409

    company = (await client.get(f"{API}/companies/{company_id}")).json()
    assert company["itAccredited"] is True


def docx_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
    return buffer.getvalue()


async def test_registry_extract_may_be_docx(
    client: AsyncClient, admin: dict[str, str], uploads: Path
) -> None:
    employer = await employer_with_company(client, "docx@fsp.ru")
    plain_zip = io.BytesIO()
    with zipfile.ZipFile(plain_zip, "w") as archive:
        archive.writestr("readme.txt", "not a document")
    refused = await client.post(
        f"{API}/companies/me/verification/documents",
        headers=employer,
        files={"file": ("extract.docx", plain_zip.getvalue(), "application/zip")},
    )
    assert refused.status_code == 400

    data = docx_bytes()
    uploaded = await client.post(
        f"{API}/companies/me/verification/documents",
        headers=employer,
        files={"file": ("Выписка Минцифры.pdf", data, "application/pdf")},
    )
    assert uploaded.status_code == 201, uploaded.text
    document = uploaded.json()["documents"][0]
    assert (document["filename"], document["kind"]) == ("Выписка Минцифры.pdf.docx", "docx")
    assert stored_files(uploads, "docx") == 1

    company_id = (await client.get(f"{API}/companies/me", headers=employer)).json()["id"]
    file = await client.get(
        f"{API}/admin/verifications/{company_id}/documents/{document['id']}", headers=admin
    )
    assert file.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert file.headers["content-disposition"].startswith("attachment;")
    assert file.headers["x-content-type-options"] == "nosniff"
    assert file.content == data


async def test_deleting_the_last_document_drops_the_request(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    employer = await employer_with_company(client, "withdraw@fsp.ru")
    first = await client.post(
        f"{API}/companies/me/verification/documents",
        headers=employer,
        files={"file": ("one.pdf", PDF, "application/pdf")},
    )
    second = await client.post(
        f"{API}/companies/me/verification/documents",
        headers=employer,
        files={"file": ("two.pdf", PDF, "application/pdf")},
    )
    assert second.status_code == 201, second.text
    kept, dropped = second.json()["documents"]
    company_id = (await client.get(f"{API}/companies/me", headers=employer)).json()["id"]

    still = await client.delete(
        f"{API}/companies/me/verification/documents/{dropped['id']}", headers=employer
    )
    assert still.json()["status"] == "pending"
    assert [item["id"] for item in still.json()["documents"]] == [kept["id"]]
    assert (await client.get(f"{API}/admin/verifications/pending-count", headers=admin)).json() == 1

    gone = await client.delete(
        f"{API}/companies/me/verification/documents/{kept['id']}", headers=employer
    )
    assert gone.status_code == 200, gone.text
    assert gone.json()["status"] is None
    assert gone.json()["documents"] == []
    assert (await client.get(f"{API}/admin/verifications/pending-count", headers=admin)).json() == 0
    queue = (await client.get(f"{API}/admin/verifications?status=pending", headers=admin)).json()
    assert queue["items"] == []
    missing = await client.get(f"{API}/admin/verifications/{company_id}", headers=admin)
    assert missing.status_code == 404
    refused = await client.post(
        f"{API}/admin/verifications/{company_id}/reject",
        headers=admin,
        json={"reason": "Нечего проверять"},
    )
    assert refused.status_code == 404
    # The first upload is only here so a failed assertion names the response.
    assert first.status_code == 201


def stored_files(root: Path, kind: str) -> int:
    return len(list(root.rglob(f"*.{kind}")))


def stored_pdfs(root: Path) -> int:
    return stored_files(root, "pdf")


def test_clean_filename() -> None:
    assert clean_filename("../../etc/passwd") == "passwd.pdf"
    assert clean_filename('C:\\docs\\"устав".PDF') == "устав.PDF"
    assert clean_filename(None) == "document.pdf"
    assert clean_filename("выписка.docx", "docx") == "выписка.docx"


def test_sniff_document() -> None:
    assert sniff_document(PDF) == "pdf"
    assert sniff_document(docx_bytes()) == "docx"
    assert sniff_document(b"PK\x03\x04broken") is None
    assert sniff_document(b"\x89PNG\r\n\x1a\n") is None


# ── Admin account ───────────────────────────────────────────────────────────────────────────────


async def test_ensure_admin(sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    async with sessionmaker() as session:
        assert await ensure_admin(session, " Root@FSP.ru ", "long-enough-password") is True
        assert await ensure_admin(session, "root@fsp.ru", "another-long-password") is False
        with pytest.raises(AdminSetupError):
            await ensure_admin(session, "root2@fsp.ru", "short")
        session.add(User(email="cand@fsp.ru", password_hash="x", role=UserRole.CANDIDATE))
        await session.flush()
        with pytest.raises(AdminSetupError):
            await ensure_admin(session, "cand@fsp.ru", "long-enough-password")
        admin = await session.scalar(select(User).where(User.email == "root@fsp.ru"))
        assert admin is not None
        assert (admin.role, admin.is_email_verified) == (UserRole.ADMIN, True)


# ── Live suspicion signals ──────────────────────────────────────────────────────────────────────


async def _signal(client: AsyncClient, admin: dict[str, str], code: str) -> dict[str, Any]:
    page = await client.get(f"{API}/admin/analytics/employers?signal={code}", headers=admin)
    assert page.status_code == 200, page.text
    items: list[dict[str, Any]] = page.json()["items"]
    assert items, page.text
    assert code in items[0]["signals"]
    assert items[0]["caseStatus"] == "flagged"
    return items[0]


async def test_reaction_flapping_flags_without_a_recount(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    employer = await employer_with_company(client, "flap@fsp.ru")
    _token, candidate_id = await candidate_with_resume(client, "flap-dev@fsp.ru")
    for _ in range(5):
        liked = await client.put(
            f"{API}/candidates/{candidate_id}/reaction",
            headers=employer,
            json={"kind": "like"},
        )
        cleared = await client.delete(f"{API}/candidates/{candidate_id}/reaction", headers=employer)
        assert liked.status_code == 200, liked.text
        assert cleared.status_code == 204, cleared.text
    row = await _signal(client, admin, "reaction_flapping")
    assert row["name"] == "ООО Проверка"


async def test_requisites_churn_and_unknown_industry(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    email = "churn@fsp.ru"
    employer = await employer_with_company(client, email)
    inn = make_inn(email)
    for index in range(5):
        saved = await client.put(
            f"{API}/companies/me",
            headers=employer,
            json={**COMPANY, "inn": inn, "name": f"Смена {index}"},
        )
        assert saved.status_code == 200, saved.text
    await _signal(client, admin, "requisites_churn")

    rejected = await client.put(
        f"{API}/companies/me",
        headers=employer,
        json={**COMPANY, "inn": inn, "industry": "Космос"},
    )
    assert rejected.status_code == 400
    assert rejected.json()["error"]["message"] == "Выберите направление из списка"
    await _signal(client, admin, "invalid_industry")


async def test_digit_only_vacancy_is_rejected_and_counted(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    employer = await employer_with_company(client, "digits@fsp.ru")
    body = {**VACANCY, "title": "12345", "description": "1" * 150}
    for _ in range(2):
        created = await client.post(f"{API}/vacancies", headers=employer, json=body)
        assert created.status_code == 400, created.text
        assert created.json()["error"]["message"] == "Опишите вакансию словами"
    await _signal(client, admin, "junk_vacancies")


async def test_meeting_cancellations_flag_the_company(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    employer = await employer_with_company(client, "meets@fsp.ru")
    candidate, candidate_id = await candidate_with_resume(client, "meets-dev@fsp.ru")
    vacancy = await client.post(f"{API}/vacancies", headers=employer, json=VACANCY)
    assert vacancy.status_code == 201, vacancy.text
    liked = await client.put(
        f"{API}/vacancies/{vacancy.json()['id']}/reaction",
        headers=bearer(candidate),
        json={"kind": "like"},
    )
    assert liked.status_code == 200, liked.text
    start = datetime.now(UTC) + timedelta(days=3)
    for _ in range(5):
        created = await client.post(
            f"{API}/calendar/events",
            headers=employer,
            json={
                "candidateId": candidate_id,
                "startsAt": start.isoformat(),
                "endsAt": (start + timedelta(hours=1)).isoformat(),
            },
        )
        assert created.status_code == 201, created.text
        cancelled = await client.delete(
            f"{API}/calendar/events/{created.json()['id']}", headers=employer
        )
        assert cancelled.status_code == 204, cancelled.text
    await _signal(client, admin, "meeting_churn")


async def test_employer_attachments_flag_the_company(
    client: AsyncClient, admin: dict[str, str], tmp_path: Path
) -> None:
    settings = get_settings().model_copy(update={"upload_dir": str(tmp_path)})

    def factory(session: SessionDep, hub: NotificationHubDep) -> ChatService:
        return ChatService(
            conversations=ConversationRepository(session),
            reactions=ReactionRepository(session),
            companies=CompanyRepository(session),
            candidates=CandidateRepository(session),
            vacancies=VacancyRepository(session),
            meetings=MeetingRepository(session),
            settings=settings,
            notifications=hub,
            activity=ActivityRecorder(session),
        )

    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_chat_service] = factory

    employer = await employer_with_company(client, "media@fsp.ru")
    vacancy = await client.post(f"{API}/vacancies", headers=employer, json=VACANCY)
    assert vacancy.status_code == 201, vacancy.text
    candidate, candidate_id = await candidate_with_resume(client, "media-dev@fsp.ru")
    liked = await client.put(
        f"{API}/candidates/{candidate_id}/reaction", headers=employer, json={"kind": "like"}
    )
    assert liked.status_code == 200, liked.text
    inbound = (await client.get(f"{API}/responses/inbound", headers=bearer(candidate))).json()
    answered = await client.post(
        f"{API}/responses/inbound/companies/{inbound[0]['companyId']}/respond",
        headers=bearer(candidate),
    )
    assert answered.status_code == 204, answered.text
    chats = (await client.get(f"{API}/conversations", headers=employer)).json()
    for _ in range(10):
        sent = await client.post(
            f"{API}/conversations/{chats[0]['id']}/attachments",
            headers=employer,
            files={"file": ("note.pdf", PDF, "application/pdf")},
        )
        assert sent.status_code == 201, sent.text
    await _signal(client, admin, "chat_media_spam")
    app.dependency_overrides.pop(get_chat_service, None)


# ── Bans that block ─────────────────────────────────────────────────────────────────────────────


CSRF = {"X-Kadry-Request": "1"}


def _banned(response: Any, reason: str) -> None:
    assert response.status_code == 403, response.text
    error = response.json()["error"]
    assert error["code"] == "account_banned"
    assert error["details"]["reason"] == reason
    assert error["details"]["supportEmail"] == "support@kadry.local"


async def test_a_ban_blocks_login_refresh_and_requests(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    specialist = await register_and_login(client, "banned-dev@fsp.ru")
    added = await client.post(
        f"{API}/admin/banlist",
        headers=admin,
        json={"email": "banned-dev@fsp.ru", "reason": "Спам"},
    )
    assert added.status_code == 201, added.text
    assert added.json()["accounts"] == [{"email": "banned-dev@fsp.ru", "role": "candidate"}]
    _banned(await client.get(f"{API}/users/me", headers=bearer(specialist)), "Спам")
    _banned(await client.post(f"{API}/auth/refresh", headers=CSRF), "Спам")
    _banned(
        await client.post(
            f"{API}/auth/login", json={"email": "banned-dev@fsp.ru", "password": PASSWORD}
        ),
        "Спам",
    )

    employer = await employer_with_company(client, "banned-boss@fsp.ru")
    added = await client.post(
        f"{API}/admin/banlist",
        headers=admin,
        json={"email": "banned-boss@fsp.ru", "reason": "Фиктивные вакансии"},
    )
    assert added.status_code == 201, added.text
    assert added.json()["accounts"][0]["role"] == "employer"
    _banned(await client.get(f"{API}/companies/me", headers=employer), "Фиктивные вакансии")
    _banned(await client.post(f"{API}/auth/refresh", headers=CSRF), "Фиктивные вакансии")
    _banned(
        await client.post(
            f"{API}/auth/login", json={"email": "banned-boss@fsp.ru", "password": PASSWORD}
        ),
        "Фиктивные вакансии",
    )

    ban_id = (await client.get(f"{API}/admin/banlist?q=banned-boss", headers=admin)).json()[
        "items"
    ][0]["id"]
    lifted = await client.post(
        f"{API}/admin/banlist/{ban_id}/unban", headers=admin, json={"reason": "Ошибка"}
    )
    assert lifted.status_code == 200, lifted.text
    back = await client.post(
        f"{API}/auth/login", json={"email": "banned-boss@fsp.ru", "password": PASSWORD}
    )
    assert back.status_code == 200, back.text


async def test_a_domain_ban_blocks_registration(client: AsyncClient, admin: dict[str, str]) -> None:
    added = await client.post(
        f"{API}/admin/banlist",
        headers=admin,
        json={"emailDomain": "blocked.example", "reason": "Домен закрыт"},
    )
    assert added.status_code == 201, added.text
    registered = await client.post(
        f"{API}/auth/register",
        json={
            "email": "newbie@blocked.example",
            "password": PASSWORD,
            "role": "candidate",
            "personalDataConsent": True,
        },
    )
    _banned(registered, "Домен закрыт")
