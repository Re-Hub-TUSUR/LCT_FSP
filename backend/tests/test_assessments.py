import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.dependencies.services import get_code_runner
from app.models import AssessmentAttempt, AssessmentStatus, CandidateProfile, Grade, TaskKind
from app.schemas.assessment import RulesComposition
from app.seed.assessment import code_tasks, grade_tests, quiz_tasks, seed_assessment_bank
from app.services.assessment_bank import judge, normalize_output
from app.services.assessments import _draw
from app.services.categories import SPECIALIZATIONS
from app.services.code_runner import Execution
from tests.conftest import API, bearer, create_admin, login, register_and_login

HIDDEN_INPUT = "hidden-input-marker"


class StubRunner:
    """The "program" is its own source: `echo` prints stdin, the rest fail in a named way."""

    available = True

    def __init__(self) -> None:
        self.inputs: list[str] = []

    async def run(self, *, compiler: str, code: str, stdin: str) -> Execution:
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
        "quiz": {"options": [f"right {question}", "wrong a", "wrong b"], "correct": [0]},
        **extra,
    }


def code(title: str = "Echo", **extra: Any) -> dict[str, Any]:
    return {
        "kind": "code",
        "difficulty": "easy",
        "topic": "io",
        "title": title,
        "statement": "Print the input.",
        "code": {
            "groups": [
                {"input": "open", "expected": "open", "hidden": False},
                {"input": HIDDEN_INPUT, "expected": HIDDEN_INPUT, "hidden": True},
                {"input": HIDDEN_INPUT + "2", "expected": HIDDEN_INPUT + "2", "hidden": True},
            ],
            "reference": {"language": "python-3.14", "code": "echo"},
        },
        **extra,
    }


async def admin_token(client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]) -> str:
    await create_admin(sessionmaker, "admin@fsp.ru")
    return await login(client, "admin@fsp.ru")


async def platform_test(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], *, with_code: bool = True
) -> None:
    """Junior template: two questions and (optionally) one code task."""
    headers = bearer(await admin_token(client, sessionmaker))
    for payload in (quiz("Q1"), quiz("Q2"), *([code()] if with_code else [])):
        created = await client.post(f"{API}/admin/assessment-tasks", headers=headers, json=payload)
        assert created.status_code == 201, created.text
    rules = [{"kind": "quiz", "count": 2}, *([{"kind": "code", "count": 1}] if with_code else [])]
    created = await client.post(
        f"{API}/admin/assessment-tests",
        headers=headers,
        json={
            "title": "Junior",
            "grade": "junior",
            "durationMinutes": 25,
            "composition": {"mode": "rules", "rules": rules},
        },
    )
    assert created.status_code == 201, created.text


async def start(client: AsyncClient, token: str) -> dict[str, Any]:
    response = await client.post(
        f"{API}/assessments/attempts",
        headers=bearer(token),
        json={"specialization": "backend", "grade": "junior"},
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
                for index, option in enumerate(task["options"])
                if option.startswith("right") == right
            )
            payload: dict[str, Any] = {"taskId": task["id"], "selected": [position]}
        else:
            payload = {"taskId": task["id"], "language": "python-3.14", "code": program}
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
    assert before.json()["status"] == "not_taken"

    attempt = await start(client, token)
    assert {task["kind"] for task in attempt["tasks"]} == {"quiz", "code"}
    # Nothing that would give the answers away.
    raw = str(attempt)
    assert "correct" not in raw
    assert HIDDEN_INPUT not in raw
    assert "reference" not in raw
    code_task = next(task for task in attempt["tasks"] if task["kind"] == "code")
    assert code_task["samples"] == [{"input": "open", "expected": "open"}]

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
    assert all(task["selected"] or task["draft"] for task in reloaded.json()["tasks"]), (
        "saved answers come back with the attempt"
    )

    finished = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/finish", headers=bearer(token)
    )
    assert finished.status_code == 200, finished.text
    assert (finished.json()["status"], finished.json()["score"]) == ("passed", 100.0)
    assert sorted(runner.inputs[1:]) == [HIDDEN_INPUT, HIDDEN_INPUT + "2"]

    status = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
    assert (status["status"], status["specialization"], status["grade"]) == (
        "passed",
        "backend",
        "junior",
    )
    # A confirmed grade can be changed only after the cooldown.
    assert status["nextAttemptAt"] is not None
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
    assert (status["status"], status["grade"], status["specialization"]) == ("failed", None, None)
    assert status["nextAttemptAt"] is not None
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
        json={"taskId": attempt["tasks"][0]["id"], "selected": [0]},
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

    assert (status["status"], status["activeAttemptId"]) == ("failed", None)
    assert status["history"][0]["status"] == "expired"
    assert status["nextAttemptAt"] is not None


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
    """Without ONLINECOMPILER_API_KEY the real runner refuses instead of guessing a verdict."""
    await platform_test(client, sessionmaker)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)
    task = next(task for task in attempt["tasks"] if task["kind"] == "code")

    status = await client.get(f"{API}/assessments/me", headers=bearer(token))
    ran = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/run",
        headers=bearer(token),
        json={"taskId": task["id"], "language": "python-3.14", "code": "print(1)"},
    )

    assert status.json()["codeRunnerAvailable"] is False
    assert (ran.status_code, ran.json()["error"]["code"]) == (503, "code_runner_unavailable")


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
    broken["code"]["reference"]["code"] = "wrong"
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
    no_hidden["code"]["groups"] = [
        {"input": "a", "expected": "a", "hidden": False},
        {"input": "b", "expected": "b", "hidden": False},
    ]
    too_long = code()
    too_long["code"]["groups"][0]["expected"] = "x" * 901
    two_correct = quiz("Q")
    two_correct["quiz"]["correct"] = [0, 1]

    responses = [
        await client.post(f"{API}/admin/assessment-tasks", headers=headers, json=payload)
        for payload in (
            no_hidden,
            too_long,
            two_correct,
            quiz("Q", specializations=["astrology"]),
            {**quiz("Q"), "code": code()["code"]},
        )
    ]

    assert [response.status_code for response in responses] == [422, 422, 422, 400, 422]


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


def test_starter_bank_covers_every_category() -> None:
    """Every specialization × grade gets a full variant with a code task of the right level."""
    pool = [*quiz_tasks(), *code_tasks()]
    assert len({task.id for task in pool}) == len(pool), "questions and task keys are unique"
    expected_code = {
        Grade.INTERN: "easy",
        Grade.JUNIOR: "easy",
        Grade.MIDDLE: "medium",
        Grade.SENIOR: "hard",
        Grade.LEAD: "medium",
    }
    templates = grade_tests()
    assert {test.grade for test in templates} == set(Grade)

    for test in templates:
        assert 25 <= test.duration_minutes <= 35
        composition = RulesComposition.model_validate(test.composition)
        wanted = sum(rule.count for rule in composition.rules)
        for specialization in SPECIALIZATIONS:
            variant = _draw(composition, pool, specialization, set())
            assert len(variant) == wanted, (test.grade, specialization)
            tasks = [task for task in variant if task.kind == TaskKind.CODE]
            assert len(tasks) == 1
            assert specialization in tasks[0].specializations, (test.grade, specialization)
            assert test.grade is not None
            assert tasks[0].difficulty == expected_code[test.grade], (test.grade, specialization)


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

    assert (first.code, first.tests) == (15, 5)
    assert first.quiz > 120
    assert attempts.all() == []
