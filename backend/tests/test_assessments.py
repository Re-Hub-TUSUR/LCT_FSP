import subprocess
import sys
import time
import uuid
from collections.abc import AsyncIterator, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.admin.models import AdminAuditLog
from app.core.errors import ConflictError, NotFoundError
from app.dependencies.services import get_code_runner
from app.models import (
    AssessmentAttempt,
    AssessmentStatus,
    AssessmentTask,
    AssessmentTest,
    CandidateProfile,
    Grade,
    TaskDifficulty,
    TaskKind,
)
from app.repositories.assessment import AssessmentRepository
from app.schemas.assessment import (
    AttemptContext,
    CodeContext,
    CodePayload,
    CompositionRule,
    QuizContext,
    QuizPayload,
    RulesComposition,
)
from app.seed.assessment import (
    TEMPLATE_VERSION,
    _rows,
    _template_id,
    code_tasks,
    content_hash,
    grade_tests,
    quiz_tasks,
    seed_assessment_bank,
)
from app.seed.code_bank import run
from app.seed.code_bank.__main__ import main as build_code_bank
from app.services.assessments import _draw
from app.services.attempt_context import AttemptContextService, render_context
from app.services.categories import SPECIALIZATIONS
from app.services.code_runner import COMPILERS, CodeRunnerUnavailableError, Execution
from app.services.quiz_lint import MAX_LONGEST_SHARE, longest_share, option_warning
from app.services.task_kinds.code import CodeKind, judge, normalize_output
from app.services.task_kinds.quiz import QuizKind
from tests.conftest import API, bearer, create_admin, login, register_and_login
from tests.weak_solutions import WEAK_SOLUTIONS

HIDDEN_INPUT = "hidden-input-marker"


class StubRunner:
    """The "program" is its own source: `echo` prints stdin, the rest fail in a named way."""

    available = True

    def __init__(self) -> None:
        self.inputs: list[str] = []
        # True: the service is configured but does not answer.
        self.down = False

    async def run(self, *, compiler: str, code: str, stdin: str) -> Execution:
        if self.down:
            raise CodeRunnerUnavailableError()
        self.inputs.append(stdin)
        if code == "echo":
            return Execution(ok=True, output=stdin + "  \n", error="", time=0.1)
        if code == "crash":
            return Execution(ok=False, output="", error="Traceback", time=0.1)
        if code == "slow":
            return Execution(ok=True, output=stdin, error="", time=99.0)
        return Execution(ok=True, output="something else", error="", time=0.1)


@pytest.fixture
async def runner(client: AsyncClient) -> AsyncIterator[StubRunner]:
    stub = StubRunner()
    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_code_runner] = lambda: stub
    yield stub
    app.dependency_overrides.pop(get_code_runner)


def quiz(question: str, **extra: Any) -> dict[str, Any]:
    return {
        "kind": "quiz",
        "difficulty": "easy",
        "topic": "basics",
        "title": question,
        "statement": question,
        "payload": {"options": [f"right {question}", "wrong a", "wrong b"], "correct": [0]},
        **extra,
    }


def code(title: str = "Echo", **extra: Any) -> dict[str, Any]:
    return {
        "kind": "code",
        "difficulty": "easy",
        "topic": "io",
        "title": title,
        "statement": "Print the input.",
        "payload": {
            "groups": [
                {"input": "open", "expected": "open", "hidden": False},
                {"input": HIDDEN_INPUT, "expected": HIDDEN_INPUT, "hidden": True},
                {"input": HIDDEN_INPUT + "2", "expected": HIDDEN_INPUT + "2", "hidden": True},
            ],
            "reference": {"language": "python-3.14", "code": "echo"},
        },
        **extra,
    }


async def admin_token(
    client: AsyncClient,
    sessionmaker: async_sessionmaker[AsyncSession],
    email: str = "admin@fsp.ru",
) -> str:
    await create_admin(sessionmaker, email)
    return await login(client, email)


async def platform_test(
    client: AsyncClient,
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    with_code: bool = True,
    extra_grades: Sequence[str] = (),
    **template: Any,
) -> None:
    """Junior template: two questions and (optionally) one code task. `extra_grades` adds a twin
    template for each of those grades; `template` fields (camelCase) override the defaults."""
    headers = bearer(await admin_token(client, sessionmaker))
    for payload in (quiz("Q1"), quiz("Q2"), *([code()] if with_code else [])):
        created = await client.post(f"{API}/admin/assessment-tasks", headers=headers, json=payload)
        assert created.status_code == 201, created.text
    rules = [{"kind": "quiz", "count": 2}, *([{"kind": "code", "count": 1}] if with_code else [])]
    for grade in ("junior", *extra_grades):
        created = await client.post(
            f"{API}/admin/assessment-tests",
            headers=headers,
            json={
                "title": grade,
                "grade": grade,
                "durationMinutes": 25,
                "composition": {"mode": "rules", "rules": rules},
                **template,
            },
        )
        assert created.status_code == 201, created.text


async def start(client: AsyncClient, token: str, specialization: str = "backend") -> dict[str, Any]:
    response = await client.post(
        f"{API}/assessments/attempts",
        headers=bearer(token),
        json={"specialization": specialization, "grade": "junior"},
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def answer_all(
    client: AsyncClient, token: str, attempt: dict[str, Any], *, right: bool, program: str = "echo"
) -> None:
    for task in attempt["tasks"]:
        if task["kind"] == "quiz":
            position = next(
                index
                for index, option in enumerate(task["content"]["options"])
                if option.startswith("right") == right
            )
            answer: dict[str, Any] = {"selected": [position]}
        elif task["kind"] == "code":
            answer = {"language": "python-3.14", "code": program}
        else:
            answer = {"text": "Развёрнутый ответ"}
        payload = {"taskId": task["id"], "answer": answer}
        saved = await client.post(
            f"{API}/assessments/attempts/{attempt['id']}/answers",
            headers=bearer(token),
            json=payload,
        )
        assert saved.status_code == 204, saved.text


async def test_passed_test_confirms_the_category(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker)
    token = await register_and_login(client, "dev@fsp.ru")

    before = await client.get(f"{API}/assessments/me", headers=bearer(token))
    assert (before.json()["status"], before.json()["tracks"]) == ("not_taken", [])

    attempt = await start(client, token)
    assert {task["kind"] for task in attempt["tasks"]} == {"quiz", "code"}
    # Nothing that would give the answers away.
    raw = str(attempt)
    assert "correct" not in raw
    assert HIDDEN_INPUT not in raw
    assert "reference" not in raw
    code_task = next(task for task in attempt["tasks"] if task["kind"] == "code")
    assert code_task["content"]["samples"] == [{"input": "open", "expected": "open"}]
    assert code_task["content"]["timeLimit"] == 5

    await answer_all(client, token, attempt, right=True)

    ran = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/run",
        headers=bearer(token),
        json={"taskId": code_task["id"], "language": "python-3.14", "code": "echo"},
    )
    assert ran.status_code == 200, ran.text
    assert [result["verdict"] for result in ran.json()["results"]] == ["ok"]
    # "Run" touches only the open group.
    assert runner.inputs == ["open"]

    reloaded = await client.get(
        f"{API}/assessments/attempts/{attempt['id']}", headers=bearer(token)
    )
    assert all(task["answer"] for task in reloaded.json()["tasks"]), (
        "saved answers come back with the attempt"
    )

    finished = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/finish", headers=bearer(token)
    )
    assert finished.status_code == 200, finished.text
    assert (finished.json()["status"], finished.json()["score"]) == ("passed", 100.0)
    assert sorted(runner.inputs[1:]) == [HIDDEN_INPUT, HIDDEN_INPUT + "2"]

    status = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
    (track,) = status["tracks"]
    assert (track["status"], track["specialization"], track["grade"], track["isPrimary"]) == (
        "passed",
        "backend",
        "junior",
        True,
    )
    # The primary category is repeated at the top level for the profile page.
    assert (status["status"], status["specialization"], status["grade"]) == (
        "passed",
        "backend",
        "junior",
    )
    # A confirmed grade can be changed only after the cooldown.
    assert track["nextAttemptAt"] == status["nextAttemptAt"] is not None
    again = await client.post(
        f"{API}/assessments/attempts",
        headers=bearer(token),
        json={"specialization": "backend", "grade": "middle"},
    )
    assert again.status_code == 409

    async with sessionmaker() as session:
        profile = (await session.scalars(select(CandidateProfile))).one()
        assert profile.assessment_status == AssessmentStatus.PASSED
        assert (profile.grade, profile.assessment_score) == (Grade.JUNIOR, 100.0)


async def test_failed_test_assigns_nothing(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)
    await answer_all(client, token, attempt, right=False, program="wrong")

    finished = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/finish", headers=bearer(token)
    )

    assert (finished.json()["status"], finished.json()["score"]) == ("failed", 0.0)
    status = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
    (track,) = status["tracks"]
    assert (track["status"], track["grade"], track["isPrimary"]) == ("failed", None, False)
    assert (status["status"], status["grade"], status["specialization"]) == ("failed", None, None)
    assert track["nextAttemptAt"] is not None
    async with sessionmaker() as session:
        profile = (await session.scalars(select(CandidateProfile))).one()
        assert profile.assessment_status == AssessmentStatus.FAILED
        assert (profile.grade, profile.assessment_score) == (None, None)


async def test_score_weighs_quiz_and_code(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)
    # Quiz is right (40 %), the program crashes on every hidden group (0 of 60 %).
    await answer_all(client, token, attempt, right=True, program="crash")

    finished = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/finish", headers=bearer(token)
    )

    assert (finished.json()["status"], finished.json()["score"]) == ("failed", 40.0)
    breakdown = {item["kind"]: item["earned"] for item in finished.json()["breakdown"]}
    assert breakdown == {"quiz": 1.0, "code": 0.0}


async def test_quiz_minimum_holds_back_a_pass_on_code_alone(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker, quizMin=50)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)
    assert attempt["quizMin"] == 50
    # The code is right in full (60 points, the pass mark), the quiz is wrong from the first answer.
    answer_code = [task for task in attempt["tasks"] if task["kind"] == "code"]
    await answer_all(client, token, {**attempt, "tasks": answer_code}, right=True)

    finished = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/finish", headers=bearer(token)
    )

    body = finished.json()
    assert (body["status"], body["score"], body["quizShare"]) == ("failed", 60.0, 0.0)
    status = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
    assert status["tracks"][0]["status"] == "failed"


async def test_quiz_minimum_lets_a_good_quiz_through(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker, quizMin=50)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)
    await answer_all(client, token, attempt, right=True)

    finished = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/finish", headers=bearer(token)
    )

    assert (finished.json()["status"], finished.json()["quizShare"]) == ("passed", 100.0)


async def test_beta_test_marks_the_category_and_the_profile(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker, isBeta=True, quizMin=40)
    token = await register_and_login(client, "dev@fsp.ru")
    templates = (await client.get(f"{API}/assessments/templates", headers=bearer(token))).json()
    assert [(item["isBeta"], item["quizMin"]) for item in templates] == [(True, 40)]
    attempt = await start(client, token)
    await answer_all(client, token, attempt, right=True)

    await client.post(f"{API}/assessments/attempts/{attempt['id']}/finish", headers=bearer(token))

    status = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
    assert status["tracks"][0]["isBeta"] is True
    async with sessionmaker() as session:
        profile = (await session.scalars(select(CandidateProfile))).one()
        assert profile.assessment_beta is True


async def test_lower_grade_opens_at_once_after_a_failure(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker, extra_grades=["intern"])
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)
    await answer_all(client, token, attempt, right=False, program="wrong")
    await client.post(f"{API}/assessments/attempts/{attempt['id']}/finish", headers=bearer(token))

    status = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
    assert status["tracks"][0]["failedGrade"] == "junior"
    assert status["tracks"][0]["nextAttemptAt"] is not None

    same = await client.post(
        f"{API}/assessments/attempts",
        headers=bearer(token),
        json={"specialization": "backend", "grade": "junior"},
    )
    lower = await client.post(
        f"{API}/assessments/attempts",
        headers=bearer(token),
        json={"specialization": "backend", "grade": "intern"},
    )

    assert same.status_code == 409
    assert lower.status_code == 201, lower.text


async def test_template_edits_are_journaled(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    headers = bearer(await admin_token(client, sessionmaker))
    body = {
        "title": "Junior",
        "grade": "junior",
        "durationMinutes": 25,
        "composition": {"mode": "rules", "rules": [{"kind": "quiz", "count": 2}]},
    }
    created = await client.post(f"{API}/admin/assessment-tests", headers=headers, json=body)
    test_id = created.json()["id"]

    await client.put(
        f"{API}/admin/assessment-tests/{test_id}",
        headers=headers,
        json={**body, "passScore": 75, "quizMin": 50},
    )
    await client.delete(f"{API}/admin/assessment-tests/{test_id}", headers=headers)

    async with sessionmaker() as session:
        entries = (
            await session.scalars(
                select(AdminAuditLog)
                .where(AdminAuditLog.entity == "assessment_test")
                .order_by(AdminAuditLog.created_at)
            )
        ).all()
    assert [entry.action for entry in entries] == ["create", "update", "delete"]
    assert entries[1].changes["pass_score"] == [60, 75]
    assert entries[1].changes["quiz_min"] == [0, 50]


def test_widened_draw_is_reported() -> None:
    easy = [
        task
        for task in quiz_tasks()
        if "backend" in task.specializations and task.difficulty == TaskDifficulty.EASY
    ][:2]
    composition = RulesComposition.model_validate(
        {"rules": [{"kind": "quiz", "count": 4, "scope": "specialization", "difficulty": ["easy"]}]}
    )
    notes: list[str] = []

    variant = _draw(composition, easy, "backend", set(), notes)

    assert len(variant) == 2
    assert notes, "a short pool must be reported"
    quiet: list[str] = []
    _draw(composition, quiz_tasks(), "backend", set(), quiet)
    assert quiet == []


async def test_answers_are_closed_after_the_deadline_but_finish_still_scores(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker, with_code=False)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)
    await answer_all(client, token, attempt, right=True)
    async with sessionmaker() as session:
        row = await session.get(AssessmentAttempt, uuid.UUID(attempt["id"]))
        assert row is not None
        row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        await session.commit()

    late = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/answers",
        headers=bearer(token),
        json={"taskId": attempt["tasks"][0]["id"], "answer": {"selected": [0]}},
    )
    finished = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/finish", headers=bearer(token)
    )

    assert (late.status_code, late.json()["error"]["code"]) == (409, "attempt_expired")
    assert finished.json()["status"] == "passed"


async def test_abandoned_attempt_expires_and_counts_as_failed(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker, with_code=False)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)
    async with sessionmaker() as session:
        row = await session.get(AssessmentAttempt, uuid.UUID(attempt["id"]))
        assert row is not None
        row.expires_at = datetime.now(UTC) - timedelta(hours=1)
        await session.commit()

    status = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()

    assert (status["tracks"][0]["status"], status["activeAttemptId"]) == ("failed", None)
    assert status["history"][0]["status"] == "expired"
    assert status["tracks"][0]["nextAttemptAt"] is not None


async def test_runs_are_rate_limited(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)
    task = next(task for task in attempt["tasks"] if task["kind"] == "code")
    body = {"taskId": task["id"], "language": "python-3.14", "code": "echo"}
    url = f"{API}/assessments/attempts/{attempt['id']}/run"

    first = await client.post(url, headers=bearer(token), json=body)
    second = await client.post(url, headers=bearer(token), json=body)
    custom = await client.post(url, headers=bearer(token), json={**body, "language": "cobol"})

    assert first.json()["runsLeft"] == 19
    assert second.status_code == 429
    assert custom.status_code == 400


async def test_code_tasks_need_the_runner_key(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    """Without ONLINECOMPILER_API_KEY a test with a code task does not start at all."""
    await platform_test(client, sessionmaker)
    token = await register_and_login(client, "dev@fsp.ru")

    status = await client.get(f"{API}/assessments/me", headers=bearer(token))
    started = await client.post(
        f"{API}/assessments/attempts",
        headers=bearer(token),
        json={"specialization": "backend", "grade": "junior"},
    )
    after = await client.get(f"{API}/assessments/me", headers=bearer(token))

    assert status.json()["codeRunnerAvailable"] is False
    assert (started.status_code, started.json()["error"]["code"]) == (
        503,
        "code_runner_unavailable",
    )
    # The attempt is not burnt: nothing started, no cooldown.
    assert (after.json()["activeAttemptId"], after.json()["history"]) == (None, [])


async def finish(client: AsyncClient, token: str, attempt: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/finish", headers=bearer(token)
    )
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


async def test_specializations_keep_their_own_cooldowns(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker, with_code=False)
    token = await register_and_login(client, "dev@fsp.ru")

    failed = await start(client, token, "backend")
    await answer_all(client, token, failed, right=False)
    await finish(client, token, failed)
    # Backend is on pause after the failure; frontend is a different clock.
    blocked = await client.post(
        f"{API}/assessments/attempts",
        headers=bearer(token),
        json={"specialization": "backend", "grade": "junior"},
    )
    passed = await start(client, token, "frontend")
    await answer_all(client, token, passed, right=True)
    assert (await finish(client, token, passed))["status"] == "passed"

    status = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
    tracks = {track["specialization"]: track for track in status["tracks"]}

    assert blocked.status_code == 409
    assert list(tracks) == ["frontend", "backend"], "confirmed specializations come first"
    assert (tracks["frontend"]["status"], tracks["frontend"]["isPrimary"]) == ("passed", True)
    assert (tracks["backend"]["status"], tracks["backend"]["isPrimary"]) == ("failed", False)
    backend_wait = datetime.fromisoformat(tracks["backend"]["nextAttemptAt"])
    frontend_wait = datetime.fromisoformat(tracks["frontend"]["nextAttemptAt"])
    assert timedelta(days=6) < backend_wait - datetime.now(UTC) < timedelta(days=8)
    assert timedelta(days=89) < frontend_wait - datetime.now(UTC) < timedelta(days=91)


async def test_candidate_chooses_the_primary_category(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker, with_code=False)
    token = await register_and_login(client, "dev@fsp.ru")
    for specialization in ("backend", "frontend"):
        attempt = await start(client, token, specialization)
        await answer_all(client, token, attempt, right=True)
        await finish(client, token, attempt)

    async def primary() -> list[str]:
        status = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
        return [t["specialization"] for t in status["tracks"] if t["isPrimary"]]

    async def profile_category() -> str | None:
        async with sessionmaker() as session:
            return (await session.scalars(select(CandidateProfile))).one().specialization

    # The first confirmed category stays primary until the candidate says otherwise.
    assert (await primary(), await profile_category()) == (["backend"], "backend")

    switched = await client.put(
        f"{API}/assessments/me/primary", headers=bearer(token), json={"specialization": "frontend"}
    )
    unknown = await client.put(
        f"{API}/assessments/me/primary", headers=bearer(token), json={"specialization": "devops"}
    )

    assert switched.status_code == 200, switched.text
    assert unknown.status_code == 404
    assert (await primary(), await profile_category()) == (["frontend"], "frontend")


async def test_template_of_a_specialization_overrides_the_general_one(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker, with_code=False)
    headers = bearer(await admin_token(client, sessionmaker, "admin2@fsp.ru"))
    own = {
        "title": "Junior QA",
        "grade": "junior",
        "specialization": "qa",
        "durationMinutes": 40,
        "retryDays": 1,
        "gradeChangeDays": 30,
        "composition": {"mode": "rules", "rules": [{"kind": "quiz", "count": 1}]},
    }
    created = await client.post(f"{API}/admin/assessment-tests", headers=headers, json=own)
    without_grade = await client.post(
        f"{API}/admin/assessment-tests", headers=headers, json={**own, "grade": None}
    )
    token = await register_and_login(client, "dev@fsp.ru")

    templates = (await client.get(f"{API}/assessments/templates", headers=bearer(token))).json()
    qa = await start(client, token, "qa")
    await answer_all(client, token, qa, right=False)
    await finish(client, token, qa)
    status = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()

    assert (created.status_code, without_grade.status_code) == (201, 400)
    by_scope = {template["specialization"]: template for template in templates}
    assert by_scope["qa"] == {
        "grade": "junior",
        "specialization": "qa",
        "durationMinutes": 40,
        "passScore": 60,
        "quizMin": 0,
        "isBeta": False,
        "tasks": {"quiz": 1},
        "retryDays": 1,
        "gradeChangeDays": 30,
        "recommendScore": 85,
    }
    assert (by_scope[None]["tasks"], by_scope[None]["retryDays"]) == ({"quiz": 2}, 7)
    assert len(qa["tasks"]) == 1
    wait = datetime.fromisoformat(status["tracks"][0]["nextAttemptAt"]) - datetime.now(UTC)
    assert timedelta(hours=23) < wait < timedelta(hours=25)


async def test_attempt_of_another_candidate_is_not_found(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker, with_code=False)
    owner = await register_and_login(client, "dev@fsp.ru")
    stranger = await register_and_login(client, "other@fsp.ru")
    attempt = await start(client, owner)

    response = await client.get(
        f"{API}/assessments/attempts/{attempt['id']}", headers=bearer(stranger)
    )

    assert response.status_code == 404


async def test_reference_solution_check(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    headers = bearer(await admin_token(client, sessionmaker))
    good = await client.post(f"{API}/admin/assessment-tasks", headers=headers, json=code())
    broken = code("Broken")
    broken["payload"]["reference"]["code"] = "wrong"
    bad = await client.post(f"{API}/admin/assessment-tasks", headers=headers, json=broken)

    checked = await client.post(
        f"{API}/admin/assessment-tasks/{good.json()['id']}/check", headers=headers
    )
    failed = await client.post(
        f"{API}/admin/assessment-tasks/{bad.json()['id']}/check", headers=headers
    )

    assert checked.json()["ok"] is True
    assert len(checked.json()["groups"]) == 3
    assert failed.json()["ok"] is False
    assert {group["verdict"] for group in failed.json()["groups"]} == {"wrong_answer"}


async def test_task_payload_is_validated(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    headers = bearer(await admin_token(client, sessionmaker))
    no_hidden = code()
    no_hidden["payload"]["groups"] = [
        {"input": "a", "expected": "a", "hidden": False},
        {"input": "b", "expected": "b", "hidden": False},
    ]
    too_long = code()
    too_long["payload"]["groups"][0]["expected"] = "x" * 901
    two_correct = quiz("Q")
    two_correct["payload"]["correct"] = [0, 1]

    responses = [
        await client.post(f"{API}/admin/assessment-tasks", headers=headers, json=payload)
        for payload in (
            no_hidden,
            too_long,
            two_correct,
            quiz("Q", specializations=["astrology"]),
            # The content of another kind.
            {**quiz("Q"), "payload": code()["payload"]},
            # A hand-graded task has no place in a grade test.
            {**quiz("Q"), "kind": "open", "payload": {}},
        )
    ]

    assert [response.status_code for response in responses] == [422, 422, 422, 400, 422, 400]


async def test_employer_bank_is_isolated(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    admin = bearer(await admin_token(client, sessionmaker))
    first = bearer(await register_and_login(client, "hr1@fsp.ru", role="employer"))
    second = bearer(await register_and_login(client, "hr2@fsp.ru", role="employer"))
    candidate = bearer(await register_and_login(client, "dev@fsp.ru"))
    mine = "/companies/me"
    platform_task = await client.post(
        f"{API}/admin/assessment-tasks", headers=admin, json=quiz("P")
    )
    own = await client.post(f"{API}{mine}/assessment-tasks", headers=first, json=quiz("Own"))
    assert own.status_code == 201, own.text
    assert own.json()["platform"] is False

    test = {
        "title": "Отбор в команду",
        "durationMinutes": 20,
        "composition": {"mode": "fixed", "taskIds": [own.json()["id"]]},
    }
    created = await client.post(f"{API}{mine}/assessment-tests", headers=first, json=test)
    foreign = await client.post(f"{API}{mine}/assessment-tests", headers=second, json=test)
    with_platform_task = await client.post(
        f"{API}{mine}/assessment-tests",
        headers=first,
        json={**test, "composition": {"mode": "fixed", "taskIds": [platform_task.json()["id"]]}},
    )
    by_rules = await client.post(
        f"{API}{mine}/assessment-tests",
        headers=first,
        json={**test, "composition": {"mode": "rules", "rules": [{"kind": "quiz", "count": 1}]}},
    )

    assert created.status_code == 201, created.text
    assert (foreign.status_code, with_platform_task.status_code, by_rules.status_code) == (
        400,
        400,
        400,
    )

    listed_first = await client.get(f"{API}{mine}/assessment-tasks", headers=first)
    listed_second = await client.get(f"{API}{mine}/assessment-tasks", headers=second)
    listed_admin = await client.get(f"{API}/admin/assessment-tasks", headers=admin)
    assert [task["title"] for task in listed_first.json()["items"]] == ["Own"]
    assert listed_second.json()["items"] == []
    assert [task["title"] for task in listed_admin.json()["items"]] == ["P"]

    task_url = f"{API}{mine}/assessment-tasks/{own.json()['id']}"
    stolen = await client.put(task_url, headers=second, json=quiz("Hijacked"))
    removed_by_stranger = await client.delete(task_url, headers=second)
    forbidden = await client.get(f"{API}{mine}/assessment-tasks", headers=candidate)
    removed = await client.delete(task_url, headers=first)
    assert (stolen.status_code, removed_by_stranger.status_code) == (404, 404)
    assert (forbidden.status_code, removed.status_code) == (403, 204)


# --- an attempt does not depend on what happens around it -------------------------------------


async def test_bank_edits_do_not_reach_a_started_attempt(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)
    await answer_all(client, token, attempt, right=True)

    admin = bearer(await admin_token(client, sessionmaker, "admin2@fsp.ru"))
    bank = (await client.get(f"{API}/admin/assessment-tasks", headers=admin)).json()["items"]
    first, second = (task for task in bank if task["kind"] == "quiz")
    # One question loses an option and moves the right one, the other leaves the bank.
    changed = quiz(first["title"])
    changed["payload"] = {"options": ["wrong a", f"right {first['title']}"], "correct": [1]}
    edited = await client.put(
        f"{API}/admin/assessment-tasks/{first['id']}", headers=admin, json=changed
    )
    deleted = await client.delete(f"{API}/admin/assessment-tasks/{second['id']}", headers=admin)
    assert (edited.status_code, deleted.status_code) == (200, 204)

    reread = await client.get(f"{API}/assessments/attempts/{attempt['id']}", headers=bearer(token))
    finished = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/finish", headers=bearer(token)
    )

    assert reread.status_code == 200, reread.text
    # Same tasks, same options in the same order, same answers.
    assert reread.json()["tasks"] == [
        {**task, "answer": saved["answer"]}
        for task, saved in zip(attempt["tasks"], reread.json()["tasks"], strict=True)
    ]
    assert all(task["answer"] for task in reread.json()["tasks"])
    assert (finished.json()["status"], finished.json()["score"]) == ("passed", 100.0)


async def test_code_runner_outage_on_finish_keeps_the_work(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)
    await answer_all(client, token, attempt, right=True)
    url = f"{API}/assessments/attempts/{attempt['id']}"

    runner.down = True
    finished = await client.post(f"{url}/finish", headers=bearer(token))
    late = await client.post(
        f"{url}/answers",
        headers=bearer(token),
        json={"taskId": attempt["tasks"][0]["id"], "answer": {"selected": [0]}},
    )
    waiting = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
    again = await client.post(
        f"{API}/assessments/attempts",
        headers=bearer(token),
        json={"specialization": "backend", "grade": "junior"},
    )

    # Not a failure and not an error: the answers are frozen and wait for the runner.
    assert finished.status_code == 200, finished.text
    assert (finished.json()["status"], finished.json()["score"]) == ("grading", None)
    assert late.status_code == 409
    assert (waiting["activeAttemptId"], waiting["tracks"]) == (None, [])
    assert waiting["history"][0]["status"] == "grading"
    assert again.status_code == 409, "the same specialization waits for its result"

    # The runner is back, but the retry is not due yet.
    runner.down = False
    early = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
    assert early["history"][0]["status"] == "grading"

    async with sessionmaker() as session:
        row = await session.get(AssessmentAttempt, uuid.UUID(attempt["id"]))
        assert row is not None
        row.last_run_at = datetime.now(UTC) - timedelta(minutes=5)
        await session.commit()
    graded = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()

    assert (graded["history"][0]["status"], graded["history"][0]["score"]) == ("passed", 100.0)
    assert (graded["tracks"][0]["status"], graded["tracks"][0]["grade"]) == ("passed", "junior")


async def test_last_answer_is_accepted_right_after_the_deadline(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker, with_code=False)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)
    body = {"taskId": attempt["tasks"][0]["id"], "answer": {"selected": [0]}}
    url = f"{API}/assessments/attempts/{attempt['id']}/answers"

    async def answer_after(deadline_ago: timedelta) -> int:
        async with sessionmaker() as session:
            row = await session.get(AssessmentAttempt, uuid.UUID(attempt["id"]))
            assert row is not None
            row.expires_at = datetime.now(UTC) - deadline_ago
            await session.commit()
        return (await client.post(url, headers=bearer(token), json=body)).status_code

    # The save the runner sends when the clock hits zero still lands; a later one does not.
    assert await answer_after(timedelta(seconds=3)) == 204
    assert await answer_after(timedelta(seconds=30)) == 409


async def test_one_running_attempt_is_enforced_by_the_database(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker, with_code=False)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)

    async with sessionmaker() as session:
        row = await session.get(AssessmentAttempt, uuid.UUID(attempt["id"]))
        assert row is not None
        # What a second "start" racing past the service check would write.
        session.add(
            AssessmentAttempt(
                candidate_id=row.candidate_id,
                title="twin",
                pass_score=60,
                quiz_weight=40,
                started_at=row.started_at,
                expires_at=row.expires_at,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()


# --- the next grade after a strong result ------------------------------------------------------


async def grade_template(client: AsyncClient, headers: dict[str, str], **fields: Any) -> None:
    created = await client.post(
        f"{API}/admin/assessment-tests",
        headers=headers,
        json={
            "title": "Template",
            "durationMinutes": 25,
            "composition": {"mode": "rules", "rules": [{"kind": "quiz", "count": 2}]},
            **fields,
        },
    )
    assert created.status_code == 201, created.text


async def test_strong_result_opens_the_next_grade_at_once(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker, with_code=False)
    admin = bearer(await admin_token(client, sessionmaker, "admin2@fsp.ru"))
    await grade_template(client, admin, grade="middle")
    await grade_template(client, admin, grade="senior")
    token = await register_and_login(client, "dev@fsp.ru")

    async def start_grade(grade: str) -> Any:
        return await client.post(
            f"{API}/assessments/attempts",
            headers=bearer(token),
            json={"specialization": "backend", "grade": grade},
        )

    async def track() -> dict[str, Any]:
        status = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
        result: dict[str, Any] = status["tracks"][0]
        return result

    junior = await start(client, token)
    await answer_all(client, token, junior, right=True)
    passed = await finish(client, token, junior)

    assert (passed["score"], passed["recommendedGrade"]) == (100.0, "middle")
    opened = await track()
    assert opened["recommendation"] == {"grade": "middle", "nextAttemptAt": None}
    assert opened["nextAttemptAt"] is not None, "any other grade still waits"
    # Only one step up is open: neither a retake nor a jump over a grade.
    assert [(await start_grade(grade)).status_code for grade in ("junior", "senior")] == [409, 409]

    middle = await start_grade("middle")
    assert middle.status_code == 201, middle.text
    await answer_all(client, token, middle.json(), right=False)
    failed = await finish(client, token, middle.json())

    # A failed step up costs nothing but the usual pause before another try.
    assert (failed["status"], failed["recommendedGrade"]) == ("failed", None)
    after = await track()
    assert (after["status"], after["grade"]) == ("passed", "junior")
    assert after["recommendation"]["grade"] == "middle"
    wait = datetime.fromisoformat(after["recommendation"]["nextAttemptAt"]) - datetime.now(UTC)
    assert timedelta(days=6) < wait < timedelta(days=8)
    assert (await start_grade("middle")).status_code == 409


async def test_ordinary_pass_keeps_the_grade_change_cooldown(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker, with_code=False)
    admin = bearer(await admin_token(client, sessionmaker, "admin2@fsp.ru"))
    # Two questions and a pass mark of 50: one right answer passes, but is far from strong.
    await grade_template(client, admin, grade="junior", specialization="qa", passScore=50)
    await grade_template(client, admin, grade="middle")
    token = await register_and_login(client, "dev@fsp.ru")

    attempt = await start(client, token, "qa")
    await answer_all(client, token, attempt, right=True)
    # One of the two answers is changed to a wrong one: 50 passes, but is far from "strong".
    first = attempt["tasks"][0]
    wrong = next(
        index for index, option in enumerate(first["content"]["options"]) if "wrong" in option
    )
    await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/answers",
        headers=bearer(token),
        json={"taskId": first["id"], "answer": {"selected": [wrong]}},
    )
    passed = await finish(client, token, attempt)
    status = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
    up = await client.post(
        f"{API}/assessments/attempts",
        headers=bearer(token),
        json={"specialization": "qa", "grade": "middle"},
    )

    assert (passed["status"], passed["score"], passed["recommendedGrade"]) == ("passed", 50.0, None)
    assert status["tracks"][0]["recommendation"] is None
    assert up.status_code == 409


async def test_bank_search_export_and_import(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    admin = bearer(await admin_token(client, sessionmaker))
    employer = bearer(await register_and_login(client, "hr@fsp.ru", role="employer"))
    for payload in (quiz("Что такое индекс?", topic="sql"), quiz("Что такое HTTP?"), code()):
        await client.post(f"{API}/admin/assessment-tasks", headers=admin, json=payload)

    found = await client.get(f"{API}/admin/assessment-tasks", headers=admin, params={"q": "sql"})
    by_kind = await client.get(
        f"{API}/admin/assessment-tasks", headers=admin, params={"kind": "code", "q": "ech"}
    )
    exported = (await client.get(f"{API}/admin/assessment-tasks/export", headers=admin)).json()

    assert [task["title"] for task in found.json()["items"]] == ["Что такое индекс?"]
    assert [task["title"] for task in by_kind.json()["items"]] == ["Echo"]
    # Grouped by kind, then topic.
    assert [task["title"] for task in exported] == ["Echo", "Что такое HTTP?", "Что такое индекс?"]
    assert "id" not in exported[0]
    assert exported[0]["payload"]["timeLimit"] == 5

    # The export of one bank is a valid import for another.
    imported = await client.post(
        f"{API}/companies/me/assessment-tasks/import", headers=employer, json=exported
    )
    own = await client.get(f"{API}/companies/me/assessment-tasks", headers=employer)
    assert (imported.status_code, imported.json()) == (201, {"created": 3})
    assert sorted(task["title"] for task in own.json()["items"]) == sorted(
        task["title"] for task in exported
    )
    assert all(task["platform"] is False for task in own.json()["items"])

    # One bad task cancels the whole file and names itself.
    broken = [quiz("Новый вопрос"), quiz("Плохой", specializations=["astrology"])]
    rejected = await client.post(f"{API}/admin/assessment-tasks/import", headers=admin, json=broken)
    malformed = await client.post(
        f"{API}/admin/assessment-tasks/import",
        headers=admin,
        json=[{**quiz("Q"), "payload": {"options": ["one"], "correct": [0]}}],
    )
    after = await client.get(f"{API}/admin/assessment-tasks", headers=admin)

    assert rejected.status_code == 400
    assert "№2" in rejected.json()["error"]["message"]
    assert malformed.status_code == 422
    assert after.json()["total"] == 3


def test_judge_ignores_trailing_whitespace_only() -> None:
    assert normalize_output("1 2 \r\n3\n\n") == "1 2\n3"
    ok = Execution(ok=True, output="YES\nNO\n", error="", time=0.2)
    assert judge(ok, "YES\nNO", 5) == "ok"
    assert judge(ok, "YES\nYES", 5) == "wrong_answer"
    assert judge(Execution(ok=False, output="", error="boom", time=0.1), "x", 5) == "runtime_error"
    assert judge(Execution(ok=True, output="x", error="", time=6.0), "x", 5) == "time_limit"
    assert judge(Execution(ok=False, output="", error="", time=None, killed=True), "x", 5) == (
        "time_limit"
    )


def _strict_pool(
    rule: CompositionRule, pool: Sequence[AssessmentTask], specialization: str
) -> list[AssessmentTask]:
    """Tasks a rule may take without widening its scope or difficulty."""

    def in_scope(task: AssessmentTask) -> bool:
        if rule.scope == "specialization":
            return specialization in task.specializations
        if rule.scope == "general":
            return not task.specializations
        return not task.specializations or specialization in task.specializations

    return [
        task
        for task in pool
        if task.kind == rule.kind
        and (not rule.topics or task.topic in rule.topics)
        and (not rule.difficulty or task.difficulty in rule.difficulty)
        and in_scope(task)
    ]


def test_starter_bank_covers_every_category() -> None:
    """Every specialization × grade gets a full variant, and no rule has to widen for it."""
    pool = [*quiz_tasks(), *code_tasks()]
    assert len({task.id for task in pool}) == len(pool), "questions and task keys are unique"
    expected_code = {
        Grade.INTERN: "easy",
        Grade.JUNIOR: "easy",
        Grade.MIDDLE: "medium",
        Grade.SENIOR: "hard",
        Grade.LEAD: "hard",
    }
    templates = grade_tests()
    assert {test.grade for test in templates} == set(Grade)

    for test in templates:
        assert 25 <= test.duration_minutes <= 50
        composition = RulesComposition.model_validate(test.composition)
        wanted = sum(rule.count for rule in composition.rules)
        for specialization in SPECIALIZATIONS:
            allowed = set()
            for rule in composition.rules:
                matching = _strict_pool(rule, pool, specialization)
                # A retake must be able to differ: two full sets of questions, five code tasks.
                spare = 5 if rule.kind == TaskKind.CODE else 2 * rule.count
                assert len(matching) >= spare, (test.grade, specialization, rule)
                allowed |= {task.id for task in matching}
            variant = _draw(composition, pool, specialization, set())
            assert len(variant) == wanted, (test.grade, specialization)
            assert {task.id for task in variant} <= allowed, (test.grade, specialization)
            tasks = [task for task in variant if task.kind == TaskKind.CODE]
            assert len(tasks) == 1
            assert test.grade is not None
            assert tasks[0].difficulty == expected_code[test.grade], (test.grade, specialization)


def test_starter_bank_questions_are_well_formed() -> None:
    rows = _rows("quiz")
    assert len(rows) >= 600
    for specialization, _topic, level, question, correct, *wrong in rows:
        assert specialization is None or specialization in SPECIALIZATIONS, question
        assert level in ("e", "m", "h"), question
        assert len(question) <= 200, question
        # One right option and three or four wrong ones, or a list of several right ones.
        right = [correct] if isinstance(correct, str) else correct
        options = [*right, *wrong]
        assert len(options) == len(set(options)), question
        assert 4 <= len(options) <= 6, question
        assert right, question
        assert len(wrong) >= 2, question

    # The right option must not give itself away by its length (`app.services.quiz_lint`).
    for row in rows:
        assert option_warning(row[4], row[5:]) is None, row[3]
    assert longest_share((row[4], row[5:]) for row in rows) <= MAX_LONGEST_SHARE


def test_quiz_lint_flags_a_right_option_that_is_much_longer() -> None:
    assert option_warning("A" * 10, ["b" * 10, "c" * 9, "d" * 11]) is None
    assert option_warning("A" * 30, ["b" * 10, "c" * 12, "d" * 11]) is not None
    assert longest_share([("a" * 5, ["b", "cc"]), ("a", ["bb", "c"])]) == 0.5
    assert option_warning("A" * 30, []) is None


async def test_bank_task_carries_length_warnings(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    headers = bearer(await admin_token(client, sessionmaker))

    def question(options: list[str]) -> dict[str, Any]:
        return {
            "kind": "quiz",
            "difficulty": "easy",
            "specializations": [],
            "topic": "algorithms",
            "title": "Вопрос",
            "statement": "Вопрос",
            "payload": {"options": options, "correct": [0], "multiple": False},
        }

    leaky = await client.post(
        f"{API}/admin/assessment-tasks",
        json=question(["Очень подробный и длинный верный ответ на вопрос", "нет", "да", "не знаю"]),
        headers=headers,
    )
    fair = await client.post(
        f"{API}/admin/assessment-tasks",
        json=question(
            [
                "Верный ответ среднего размера",
                "Неверный ответ тоже среднего размера",
                "Ещё один ответ среднего размера",
                "Прочий вариант такого же размера",
            ]
        ),
        headers=headers,
    )

    assert leaky.status_code == 201, leaky.text
    assert leaky.json()["warnings"]
    assert fair.status_code == 201, fair.text
    assert fair.json()["warnings"] == []


def test_reference_solutions_pass_their_own_tests() -> None:
    for item in _rows("code"):
        reference = item["reference"]
        assert reference["language"] == "python-3.14", item["key"]
        for group in item["groups"]:
            started = time.perf_counter()
            output = run(reference["code"], group["input"])
            assert normalize_output(output) == group["expected"], item["key"]
            assert time.perf_counter() - started < item["time_limit"] / 2, item["key"]


def test_grade_thresholds_are_consistent() -> None:
    for test in grade_tests():
        # A strong result must stay above a plain pass, or every pass opens the next grade.
        assert (test.recommend_score or 85) > test.pass_score, test.grade
        # The code task alone never passes the test, and the quiz minimum is not an empty word:
        # a pass on points with the code solved may still fall short of it.
        assert test.pass_score > 100 - test.quiz_weight, test.grade
        assert test.quiz_min >= 50, test.grade
        composition = RulesComposition.model_validate(test.composition)
        questions = sum(rule.count for rule in composition.rules if rule.kind == TaskKind.QUIZ)
        assert questions == (15 if test.grade in (Grade.INTERN, Grade.JUNIOR) else 25), test.grade


def test_seed_row_with_several_right_options_is_a_multiple_choice() -> None:
    right = ["Первый верный", "Второй верный"]
    assert option_warning(right, ["Неверный один", "Неверный два"]) is None
    assert option_warning(["A" * 30, "B" * 28], ["c" * 10, "d" * 12, "e" * 11]) is not None
    assert longest_share([(["aaa", "bbbb"], ["cc", "d"]), (["a", "bbbb"], ["cc", "d"])]) == 0.5


async def test_several_right_options_earn_partial_credit() -> None:
    spec = QuizKind()
    payload = QuizPayload(options=["a", "b", "c", "d", "e"], correct=[0, 1], multiple=True)
    runner = StubRunner()

    async def points(*selected: int) -> float:
        return await spec.grade(payload, {"selected": list(selected)}, runner)

    assert await points(0, 1) == 1
    assert await points(0) == 0.5
    # A wrong option takes away what a right one earned; marking everything earns nothing.
    assert await points(0, 2) == 0
    assert await points(0, 1, 2) == 0.5
    assert await points(0, 1, 2, 3, 4) == 0
    assert await points() == 0
    single = QuizPayload(options=["a", "b"], correct=[0])
    assert await spec.grade(single, {"selected": [0]}, runner) == 1
    assert await spec.grade(single, {"selected": [1]}, runner) == 0


async def test_hidden_groups_count_by_their_weights() -> None:
    spec = CodeKind()
    payload = CodePayload.model_validate(
        {
            "groups": [
                {"input": "1", "expected": "1"},
                {"input": "2", "expected": "2", "hidden": True},
                {"input": "3", "expected": "3", "hidden": True, "weight": 3},
            ]
        }
    )

    class HeavyGroupFails(StubRunner):
        async def run(self, *, compiler: str, code: str, stdin: str) -> Execution:
            return Execution(ok=True, output="?" if stdin == "3" else stdin, error="", time=0.1)

    earned = await spec.grade(
        payload, {"language": "python-3.14", "code": "echo"}, HeavyGroupFails()
    )
    assert earned == 0.25


async def test_starter_code_reaches_the_candidate(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    headers = bearer(await admin_token(client, sessionmaker))
    buggy = "print(int(input()) + 1)"
    task = code("Найди ошибку")
    task["payload"]["starter"] = {"python-3.14": buggy}
    foreign = code("Чужой язык")
    foreign["payload"] |= {"languages": ["python-3.14"], "starter": {"go-1.26": "package main"}}
    created = await client.post(f"{API}/admin/assessment-tasks", json=task, headers=headers)
    refused = await client.post(f"{API}/admin/assessment-tasks", json=foreign, headers=headers)
    assert created.status_code == 201, created.text
    assert created.json()["payload"]["starter"] == {"python-3.14": buggy}
    assert refused.status_code == 400, refused.text

    template = await client.post(
        f"{API}/admin/assessment-tests",
        headers=headers,
        json={
            "title": "junior",
            "grade": "junior",
            "durationMinutes": 25,
            "composition": {"mode": "rules", "rules": [{"kind": "code", "count": 1}]},
        },
    )
    assert template.status_code == 201, template.text
    token = await register_and_login(client, "starter@example.com")
    attempt = await start(client, token)
    (shown,) = attempt["tasks"]
    assert shown["content"]["starter"] == {"python-3.14": buggy}


def test_hidden_groups_reject_weak_solutions() -> None:
    tasks = {item["key"]: item for item in _rows("code")}
    for key, solutions in WEAK_SOLUTIONS.items():
        hidden = [group for group in tasks[key]["groups"] if group["hidden"]]
        for name, code in solutions.items():
            passed = [_runs_right(code, group, timeout=2) for group in hidden]
            assert not all(passed), f"{key}: {name} passes every hidden group"


def _runs_right(code: str, group: dict[str, Any], *, timeout: float) -> bool:
    try:
        done = subprocess.run(  # noqa: S603 - our own test programs
            [sys.executable, "-I", "-c", code],
            input=group["input"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False
    return bool(normalize_output(done.stdout) == group["expected"])


def test_code_bank_files_are_built_from_their_sources() -> None:
    assert build_code_bank(check=True) == 0


def test_variant_prefers_tasks_the_candidate_has_not_seen() -> None:
    pool = quiz_tasks()
    composition = RulesComposition.model_validate(
        {"rules": [{"kind": "quiz", "count": 3, "scope": "specialization"}]}
    )
    backend = [task for task in pool if "backend" in task.specializations]
    seen = {str(task.id) for task in backend[:-3]}

    variant = _draw(composition, pool, "backend", seen)

    assert {task.id for task in variant} == {task.id for task in backend[-3:]}


async def test_starter_bank_loads_once(sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    async with sessionmaker() as session:
        first = await seed_assessment_bank(session)
        await session.commit()
        await seed_assessment_bank(session)
        await session.commit()
        attempts = await session.scalars(select(AssessmentAttempt))

    assert (first.quiz, first.code, first.tests) == (
        len(quiz_tasks()),
        len(code_tasks()),
        len(Grade),
    )
    assert first.quiz >= 600
    assert first.code >= 55
    assert attempts.all() == []


async def _seeded_quiz(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> tuple[uuid.UUID, dict[str, Any]]:
    """Loads the bank and returns the id and the file payload of one starter question."""
    starter = quiz_tasks()[0]
    async with sessionmaker() as session:
        await seed_assessment_bank(session)
        await session.commit()
    return starter.id, dict(starter.payload)


async def test_untouched_starter_task_follows_the_files(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    task_id, file_payload = await _seeded_quiz(sessionmaker)
    async with sessionmaker() as session:
        task = await session.get(AssessmentTask, task_id)
        assert task is not None
        # The database still holds an older wording of the options and a switched-off row.
        task.payload = {**file_payload, "options": ["old right", "old a", "old b", "old c"]}
        task.seed_hash = content_hash(task)
        task.is_active = False
        await session.commit()

    async with sessionmaker() as session:
        summary = await seed_assessment_bank(session)
        await session.commit()
        task = await session.get(AssessmentTask, task_id)
        assert task is not None
        assert task.payload == file_payload
        assert task.is_active is False, "a switched-off starter task stays off"
    assert summary.updated == 1

    async with sessionmaker() as session:
        assert (await seed_assessment_bank(session)).updated == 0


async def test_edited_starter_task_is_left_alone(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    task_id, file_payload = await _seeded_quiz(sessionmaker)
    edited = {**file_payload, "options": ["admin right", "admin a", "admin b", "admin c"]}
    async with sessionmaker() as session:
        task = await session.get(AssessmentTask, task_id)
        assert task is not None
        task.payload = edited  # the hash still describes the files, the content no longer does
        await session.commit()

    async with sessionmaker() as session:
        summary = await seed_assessment_bank(session)
        await session.commit()
        task = await session.get(AssessmentTask, task_id)
        assert task is not None
        assert task.payload == edited
    assert summary.updated == 0


async def test_starter_task_loaded_before_the_hash_is_judged_by_its_timestamps(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    task_id, file_payload = await _seeded_quiz(sessionmaker)
    async with sessionmaker() as session:
        # Written by the same insert as the row itself: never edited since.
        await session.execute(
            update(AssessmentTask)
            .where(AssessmentTask.id == task_id)
            .values(
                payload={**file_payload, "options": ["old right", "old a", "old b", "old c"]},
                seed_hash=None,
                updated_at=AssessmentTask.created_at,
            )
        )
        await session.commit()

    async with sessionmaker() as session:
        await seed_assessment_bank(session)
        await session.commit()
        task = await session.get(AssessmentTask, task_id)
        assert task is not None
        assert task.payload == file_payload

    async with sessionmaker() as session:
        task = await session.get(AssessmentTask, task_id)
        assert task is not None
        task.payload = {**file_payload, "options": ["admin right", "admin a", "admin b", "admin c"]}
        task.seed_hash = None
        await session.commit()
        await session.refresh(task)
        await session.execute(
            update(AssessmentTask)
            .where(AssessmentTask.id == task_id)
            .values(updated_at=task.created_at + timedelta(days=1))
        )
        await session.commit()

    async with sessionmaker() as session:
        await seed_assessment_bank(session)
        await session.commit()
        task = await session.get(AssessmentTask, task_id)
        assert task is not None
        assert task.payload["options"][0] == "admin right"


async def test_starter_bank_switches_off_superseded_templates(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    current = _template_id("middle", TEMPLATE_VERSION)
    async with sessionmaker() as session:
        session.add(
            AssessmentTest(
                id=_template_id("middle", 1),
                title="Тест на грейд: Middle",
                grade=Grade.MIDDLE,
                duration_minutes=30,
                composition={"mode": "rules", "rules": [{"kind": "quiz", "count": 1}]},
            )
        )
        await session.commit()
        await seed_assessment_bank(session)
        await session.commit()
        active = await session.scalars(
            select(AssessmentTest.id).where(
                AssessmentTest.grade == Grade.MIDDLE, AssessmentTest.is_active.is_(True)
            )
        )

    assert active.all() == [current]


async def interview_context(
    sessionmaker: async_sessionmaker[AsyncSession], attempt: dict[str, Any]
) -> AttemptContext:
    async with sessionmaker() as session:
        service = AttemptContextService(AssessmentRepository(session))
        return await service.build(uuid.UUID(attempt["id"]))


def position(task: dict[str, Any], *, right: bool) -> int:
    """Where the candidate saw the right (or a wrong) option of a question."""
    options: list[str] = task["content"]["options"]
    return next(i for i, option in enumerate(options) if option.startswith("right") == right)


async def test_attempt_context_shows_answers_next_to_the_expected_ones(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)
    first, second = (task for task in attempt["tasks"] if task["kind"] == "quiz")
    program = next(task for task in attempt["tasks"] if task["kind"] == "code")
    shown: list[str] = second["content"]["options"]
    picked = position(second, right=False)
    answers = {
        first["id"]: {"selected": [position(first, right=True)]},
        second["id"]: {"selected": [picked]},
        program["id"]: {"language": "python-3.14", "code": "echo"},
    }
    for task_id, answer in answers.items():
        saved = await client.post(
            f"{API}/assessments/attempts/{attempt['id']}/answers",
            headers=bearer(token),
            json={"taskId": task_id, "answer": answer},
        )
        assert saved.status_code == 204, saved.text
    result = await finish(client, token, attempt)

    context = await interview_context(sessionmaker, attempt)

    assert (context.specialization, context.grade) == ("backend", Grade.JUNIOR)
    assert (context.score, context.passed) == (result["score"], result["status"] == "passed")
    assert [task.number for task in context.tasks] == [1, 2, 3]
    by_id = dict(zip((task["id"] for task in attempt["tasks"]), context.tasks, strict=True))
    outcomes = [by_id[task["id"]].outcome for task in (first, second, program)]
    assert outcomes == ["correct", "wrong", "correct"]

    wrong = by_id[second["id"]].detail
    assert isinstance(wrong, QuizContext)
    # Options come as the candidate saw them, with both marks on the right positions.
    assert [option.text for option in wrong.options] == shown
    assert [option.chosen for option in wrong.options] == [i == picked for i in range(len(shown))]
    assert [option.correct for option in wrong.options] == [
        option.startswith("right") for option in shown
    ]

    solved = by_id[program["id"]].detail
    assert isinstance(solved, CodeContext)
    assert (solved.language, solved.code) == (COMPILERS["python-3.14"], "echo")
    assert (solved.tests_passed, solved.tests_total) == (2, 2)
    assert solved.reference_code == "echo"

    text = render_context(context)
    assert f"- [выбран] {shown[picked]}" in text
    assert f"- [верный] {shown[position(second, right=True)]}" in text
    assert "Ответ кандидата: right" in text
    assert "2 из 2 закрытых тестов" in text
    assert "    echo" in text

    # A tight budget drops the correctly answered question and keeps the wrong one.
    tight = render_context(context, max_chars=len(text) - 1)
    assert len(tight) < len(text)
    assert "Ещё верных ответов опущено: 1." in tight
    assert f"- [выбран] {shown[picked]}" in tight
    assert "Ответ кандидата: right" not in tight


async def test_attempt_context_needs_a_finished_grade_test(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], runner: StubRunner
) -> None:
    await platform_test(client, sessionmaker)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)

    with pytest.raises(ConflictError):
        await interview_context(sessionmaker, attempt)
    with pytest.raises(NotFoundError):
        await interview_context(sessionmaker, {"id": str(uuid.uuid4())})

    await finish(client, token, attempt)
    context = await interview_context(sessionmaker, attempt)

    assert not context.passed
    assert {task.outcome for task in context.tasks} == {"unanswered"}
    text = render_context(context)
    assert "Кандидат не ответил." in text
    assert "Решение не отправлено." in text
    assert len(render_context(context, max_chars=200)) <= 200
