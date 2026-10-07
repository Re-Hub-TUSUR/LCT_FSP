import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.errors import ConflictError
from app.core.security import hash_password

# Imported under another name: pytest would try to collect a class called `Test…`.
from app.models import TestAssignment as Assignment
from app.repositories.assessment import AssessmentRepository
from app.seed.fixtures import SeedData, load_seed_data
from app.seed.generate import DEMO_CANDIDATE_EMAIL, DEMO_EMPLOYER_EMAIL
from app.seed.loader import seed_database, seed_id
from app.services.attempt_context import AttemptContextService
from tests.conftest import API, PASSWORD, bearer, login, register_and_login

BANK = f"{API}/companies/me"
SENT = f"{API}/companies/me/test-assignments"
INBOX = f"{API}/assessments/assignments"


@pytest.fixture
async def data(sessionmaker: async_sessionmaker[AsyncSession]) -> SeedData:
    data = load_seed_data()
    async with sessionmaker() as session:
        await seed_database(session, data, password_hash=hash_password(PASSWORD))
        await session.commit()
    return data


async def company_test(client: AsyncClient, employer: str) -> str:
    """The company's own test: one choice question and one open question."""
    tasks = [
        {
            "kind": "quiz",
            "difficulty": "easy",
            "topic": "team",
            "title": "Какой у нас стек?",
            "statement": "Какой у нас стек?",
            "payload": {"options": ["right", "wrong a", "wrong b"], "correct": [0]},
        },
        {
            "kind": "open",
            "difficulty": "medium",
            "topic": "design",
            "title": "Очередь задач",
            "statement": "Опишите, как вы спроектируете очередь задач.",
            "payload": {"maxLength": 500, "guidance": "Ретраи, идемпотентность, мониторинг"},
        },
    ]
    ids = []
    for task in tasks:
        created = await client.post(f"{BANK}/assessment-tasks", headers=bearer(employer), json=task)
        assert created.status_code == 201, created.text
        ids.append(created.json()["id"])
    test = await client.post(
        f"{BANK}/assessment-tests",
        headers=bearer(employer),
        json={
            "title": "Тестовое в команду платежей",
            "durationMinutes": 40,
            "composition": {"mode": "fixed", "taskIds": ids},
        },
    )
    assert test.status_code == 201, test.text
    return str(test.json()["id"])


async def match(client: AsyncClient, employer: str, candidate: str, candidate_id: str) -> None:
    """Mutual like: the recruiter saves the candidate, the candidate likes a vacancy."""
    mine = await client.get(f"{API}/vacancies/mine", headers=bearer(employer))
    vacancy = next(item for item in mine.json()["items"] if item["publishedAt"])
    liked = await client.put(
        f"{API}/vacancies/{vacancy['id']}/reaction",
        headers=bearer(candidate),
        json={"kind": "like"},
    )
    saved = await client.put(
        f"{API}/candidates/{candidate_id}/reaction", headers=bearer(employer), json={"kind": "like"}
    )
    assert (liked.status_code, saved.status_code) == (200, 200)


async def take(client: AsyncClient, candidate: str, assignment_id: str) -> dict[str, Any]:
    """Starts the assigned test, answers everything and finishes it."""
    started = await client.post(f"{INBOX}/{assignment_id}/start", headers=bearer(candidate))
    assert started.status_code == 201, started.text
    attempt = started.json()
    url = f"{API}/assessments/attempts/{attempt['id']}"
    for task in attempt["tasks"]:
        if task["kind"] == "quiz":
            answer: dict[str, Any] = {"selected": [task["content"]["options"].index("right")]}
        else:
            answer = {"text": "Очередь с ретраями и идемпотентными обработчиками."}
        saved = await client.post(
            f"{url}/answers",
            headers=bearer(candidate),
            json={"taskId": task["id"], "answer": answer},
        )
        assert saved.status_code == 204, saved.text
    await client.post(f"{url}/signals", headers=bearer(candidate), json={"kind": "paste"})
    finished = await client.post(f"{url}/finish", headers=bearer(candidate))
    assert finished.status_code == 200, finished.text
    result: dict[str, Any] = finished.json()
    return result


async def test_test_is_sent_only_after_a_match(client: AsyncClient, data: SeedData) -> None:
    employer = await login(client, DEMO_EMPLOYER_EMAIL)
    candidate = await login(client, DEMO_CANDIDATE_EMAIL)
    candidate_id = str(seed_id("candidate", data.candidates[0].key))
    body = {"testId": await company_test(client, employer), "candidateId": candidate_id}

    async def matched() -> bool | None:
        profile = await client.get(f"{API}/candidates/{candidate_id}", headers=bearer(employer))
        flag: bool | None = profile.json()["matched"]
        return flag

    before = await client.post(SENT, headers=bearer(employer), json=body)
    assert (before.status_code, await matched()) == (409, False)

    await match(client, employer, candidate, candidate_id)
    sent = await client.post(
        SENT, headers=bearer(employer), json={**body, "message": " Ждём до пятницы "}
    )
    twice = await client.post(SENT, headers=bearer(employer), json=body)
    inbox = (await client.get(INBOX, headers=bearer(candidate))).json()

    assert (sent.status_code, twice.status_code, await matched()) == (201, 409, True)
    assert sent.json()["status"] == "sent"
    assert (sent.json()["tasksCount"], sent.json()["durationMinutes"]) == (2, 40)
    assert [item["id"] for item in inbox] == [sent.json()["id"]]
    assert (inbox[0]["company"]["name"], inbox[0]["message"]) == ("ПэйФлоу", "Ждём до пятницы")
    due = datetime.fromisoformat(inbox[0]["dueAt"]) - datetime.now(UTC)
    assert timedelta(days=6) < due < timedelta(days=8)


async def test_candidate_takes_the_test_and_the_company_reviews_it(
    client: AsyncClient, data: SeedData
) -> None:
    employer = await login(client, DEMO_EMPLOYER_EMAIL)
    candidate = await login(client, DEMO_CANDIDATE_EMAIL)
    candidate_id = str(seed_id("candidate", data.candidates[0].key))
    await match(client, employer, candidate, candidate_id)
    sent = await client.post(
        SENT,
        headers=bearer(employer),
        json={"testId": await company_test(client, employer), "candidateId": candidate_id},
    )
    assignment_id = sent.json()["id"]
    tracks_before = (await client.get(f"{API}/assessments/me", headers=bearer(candidate))).json()

    running = await client.post(f"{INBOX}/{assignment_id}/start", headers=bearer(candidate))
    hidden = await client.get(f"{SENT}/{assignment_id}", headers=bearer(employer))
    revoked = await client.delete(f"{SENT}/{assignment_id}", headers=bearer(employer))
    # Nothing of a running attempt reaches the company, and a started test stays.
    assert running.status_code == 201, running.text
    assert "guidance" not in running.text
    assert (hidden.json()["status"], hidden.json()["tasks"]) == ("in_progress", [])
    assert revoked.status_code == 409

    attempt = running.json()
    url = f"{API}/assessments/attempts/{attempt['id']}"
    for task in attempt["tasks"]:
        answer: dict[str, Any] = (
            {"selected": [task["content"]["options"].index("right")]}
            if task["kind"] == "quiz"
            else {"text": "Очередь с ретраями."}
        )
        await client.post(
            f"{url}/answers",
            headers=bearer(candidate),
            json={"taskId": task["id"], "answer": answer},
        )
    too_long = await client.post(
        f"{url}/answers",
        headers=bearer(candidate),
        json={"taskId": attempt["tasks"][1]["id"], "answer": {"text": "x" * 501}},
    )
    await client.post(f"{url}/signals", headers=bearer(candidate), json={"kind": "paste"})
    finished = (await client.post(f"{url}/finish", headers=bearer(candidate))).json()

    assert too_long.status_code == 400
    # The open answer waits for a person: no score yet.
    assert (finished["status"], finished["score"]) == ("awaiting_review", None)

    detail = (await client.get(f"{SENT}/{assignment_id}", headers=bearer(employer))).json()
    quiz, opened = detail["tasks"]
    assert (detail["status"], detail["score"], detail["pasteCount"]) == ("review", None, 1)
    assert (quiz["points"], quiz["manual"]) == (1.0, False)
    assert quiz["review"] == {
        "options": ["right", "wrong a", "wrong b"],
        "correct": [0],
        "selected": [0],
    }
    assert (opened["points"], opened["manual"]) == (None, True)
    assert opened["review"] == {
        "text": "Очередь с ретраями.",
        "guidance": "Ретраи, идемпотентность, мониторинг",
    }

    not_manual = await client.put(
        f"{SENT}/{assignment_id}/review",
        headers=bearer(employer),
        json={"grades": [{"taskId": quiz["id"], "points": 0}]},
    )
    reviewed = await client.put(
        f"{SENT}/{assignment_id}/review",
        headers=bearer(employer),
        json={"grades": [{"taskId": opened["id"], "points": 0.5, "comment": "Нет про мониторинг"}]},
    )

    assert not_manual.status_code == 400
    assert reviewed.status_code == 200, reviewed.text
    # (1 + 0.5) / 2 of the non-code share, which is the whole test here.
    assert (reviewed.json()["status"], reviewed.json()["score"]) == ("done", 75.0)
    assert reviewed.json()["tasks"][1]["comment"] == "Нет про мониторинг"
    inbox = (await client.get(INBOX, headers=bearer(candidate))).json()
    assert (inbox[0]["status"], inbox[0]["score"], inbox[0]["passScore"]) == ("done", 75.0, 60)

    # The tasks may leave the bank: what the candidate answered stays with the attempt.
    for task in (await client.get(f"{BANK}/assessment-tasks", headers=bearer(employer))).json()[
        "items"
    ]:
        gone = await client.delete(
            f"{BANK}/assessment-tasks/{task['id']}", headers=bearer(employer)
        )
        assert gone.status_code == 204
    kept = (await client.get(f"{SENT}/{assignment_id}", headers=bearer(employer))).json()
    assert kept["tasks"] == reviewed.json()["tasks"]

    # A company's test neither confirms a category nor starts a cooldown.
    after = (await client.get(f"{API}/assessments/me", headers=bearer(candidate))).json()
    assert after["tracks"] == tracks_before["tracks"]
    assert after["history"][0]["assignmentId"] == assignment_id
    assert after["history"][0]["status"] == "passed"


async def test_assignments_are_private_and_time_bound(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], data: SeedData
) -> None:
    employer = await login(client, DEMO_EMPLOYER_EMAIL)
    candidate = await login(client, DEMO_CANDIDATE_EMAIL)
    stranger = await register_and_login(client, "stranger@fsp.ru")
    rival = await register_and_login(client, "rival@fsp.ru", role="employer")
    candidate_id = str(seed_id("candidate", data.candidates[0].key))
    await match(client, employer, candidate, candidate_id)
    test_id = await company_test(client, employer)
    sent = await client.post(
        SENT, headers=bearer(employer), json={"testId": test_id, "candidateId": candidate_id}
    )
    assignment_id = sent.json()["id"]

    foreign_test = await client.post(
        SENT, headers=bearer(rival), json={"testId": test_id, "candidateId": candidate_id}
    )
    by_rival = await client.get(f"{SENT}/{assignment_id}", headers=bearer(rival))
    by_stranger = await client.post(f"{INBOX}/{assignment_id}/start", headers=bearer(stranger))
    by_employer = await client.post(f"{INBOX}/{assignment_id}/start", headers=bearer(employer))
    assert (foreign_test.status_code, by_rival.status_code, by_stranger.status_code) == (
        409,  # no company profile yet
        404,
        404,
    )
    assert by_employer.status_code == 403
    assert (await client.get(INBOX, headers=bearer(stranger))).json() == []
    assert (await client.get(SENT, headers=bearer(rival))).json() == []

    async with sessionmaker() as session:
        row = (await session.scalars(select(Assignment))).one()
        row.due_at = datetime.now(UTC) - timedelta(hours=1)
        await session.commit()

    late = await client.post(f"{INBOX}/{assignment_id}/start", headers=bearer(candidate))
    inbox = (await client.get(INBOX, headers=bearer(candidate))).json()
    again = await client.post(
        SENT, headers=bearer(employer), json={"testId": test_id, "candidateId": candidate_id}
    )
    declined = await client.post(f"{INBOX}/{again.json()['id']}/decline", headers=bearer(candidate))
    removed = await client.delete(f"{SENT}/{again.json()['id']}", headers=bearer(employer))

    assert (late.status_code, inbox[0]["status"]) == (409, "expired")
    # An expired one does not block sending the test again.
    assert again.status_code == 201, again.text
    assert (declined.json()["status"], removed.status_code) == ("declined", 204)


async def test_company_test_scores_itself_without_open_questions(
    client: AsyncClient, data: SeedData
) -> None:
    employer = await login(client, DEMO_EMPLOYER_EMAIL)
    candidate = await login(client, DEMO_CANDIDATE_EMAIL)
    candidate_id = str(seed_id("candidate", data.candidates[0].key))
    await match(client, employer, candidate, candidate_id)
    task = await client.post(
        f"{BANK}/assessment-tasks",
        headers=bearer(employer),
        json={
            "kind": "quiz",
            "difficulty": "easy",
            "topic": "team",
            "title": "Q",
            "statement": "Q",
            "payload": {"options": ["right", "wrong"], "correct": [0]},
        },
    )
    test = await client.post(
        f"{BANK}/assessment-tests",
        headers=bearer(employer),
        json={
            "title": "Быстрый скрининг",
            "durationMinutes": 10,
            "composition": {"mode": "fixed", "taskIds": [task.json()["id"]]},
        },
    )
    sent = await client.post(
        SENT,
        headers=bearer(employer),
        json={"testId": test.json()["id"], "candidateId": candidate_id},
    )

    finished = await take(client, candidate, sent.json()["id"])
    detail = (await client.get(f"{SENT}/{sent.json()['id']}", headers=bearer(employer))).json()

    assert (finished["status"], finished["score"]) == ("passed", 100.0)
    assert (detail["status"], detail["score"], detail["pasteCount"]) == ("done", 100.0, 1)


async def test_assigned_test_gives_no_interview_context(
    client: AsyncClient, data: SeedData, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    employer = await login(client, DEMO_EMPLOYER_EMAIL)
    candidate = await login(client, DEMO_CANDIDATE_EMAIL)
    candidate_id = str(seed_id("candidate", data.candidates[0].key))
    await match(client, employer, candidate, candidate_id)
    sent = await client.post(
        SENT,
        headers=bearer(employer),
        json={"testId": await company_test(client, employer), "candidateId": candidate_id},
    )
    result = await take(client, candidate, sent.json()["id"])

    # The follow-up interview belongs to grade tests: a company reviews its own test itself.
    async with sessionmaker() as session:
        service = AttemptContextService(AssessmentRepository(session))
        with pytest.raises(ConflictError):
            await service.build(uuid.UUID(result["id"]))
