"""AI interview: working code holds the grade until the answers about it show understanding."""

from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.dependencies.services import get_interviewer
from app.schemas.assessment import InterviewMark, InterviewQuestionState
from tests.conftest import API, bearer, register_and_login
from tests.test_assessments import (  # noqa: F401 - `runner` is a fixture used by name
    answer_all,
    platform_test,
    runner,
    start,
)

UNDERSTANDS = "понимаю"


class StubInterviewer:
    """Asks two questions; marks an answer high when it says it understands."""

    available = True
    name = "stub"

    def __init__(self) -> None:
        self.codes: list[str] = []

    async def ask(self, code: str, tasks: dict[int, str]) -> list[InterviewQuestionState]:
        self.codes.append(code)
        task, title = next(iter(tasks.items()))
        return [
            InterviewQuestionState(task=task, task_title=title, text=f"Вопрос {number}")
            for number in (1, 2)
        ]

    async def mark(
        self, code: str, questions: list[InterviewQuestionState], answers: list[str]
    ) -> tuple[list[InterviewMark], str]:
        marks = [
            InterviewMark(number=number, score=90 if UNDERSTANDS in answer else 10, comment="")
            for number, answer in enumerate(answers, 1)
        ]
        return marks, "Итог"


@pytest.fixture
async def interviewer(client: AsyncClient) -> AsyncIterator[StubInterviewer]:
    stub = StubInterviewer()
    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_interviewer] = lambda: stub
    yield stub
    app.dependency_overrides.pop(get_interviewer)


async def passed_on_points(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], email: str
) -> tuple[str, dict[str, Any]]:
    await platform_test(client, sessionmaker)
    token = await register_and_login(client, email)
    attempt = await start(client, token)
    await answer_all(client, token, attempt, right=True)
    finished = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/finish", headers=bearer(token)
    )
    assert (finished.json()["status"], finished.json()["score"]) == ("interview", 100.0)
    return token, attempt


@pytest.mark.usefixtures("runner")
async def test_good_answers_confirm_the_grade(
    client: AsyncClient,
    sessionmaker: async_sessionmaker[AsyncSession],
    interviewer: StubInterviewer,
) -> None:
    token, attempt = await passed_on_points(client, sessionmaker, "interview-ok@fsp.ru")
    url = f"{API}/assessments/attempts/{attempt['id']}/interview"

    waiting = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
    assert (waiting["interviewAttemptId"], waiting["tracks"]) == (attempt["id"], [])

    asked = (await client.get(url, headers=bearer(token))).json()
    assert [question["text"] for question in asked["questions"]] == ["Вопрос 1", "Вопрос 2"]
    assert asked["deadline"] is not None
    # The model reads the candidate's working code, not the quiz.
    (code,) = interviewer.codes
    assert "Закрытые тесты пройдены: 2 из 2" in code
    assert "Q1" not in code

    answered = await client.post(
        url, headers=bearer(token), json={"answers": [UNDERSTANDS, f"{UNDERSTANDS} и это"]}
    )
    assert answered.status_code == 200, answered.text
    assert answered.json()["result"]["passed"] is True

    status = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
    assert (status["status"], status["grade"], status["interviewAttemptId"]) == (
        "passed",
        "junior",
        None,
    )


@pytest.mark.usefixtures("runner", "interviewer")
async def test_answers_without_understanding_fail_the_test(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    token, attempt = await passed_on_points(client, sessionmaker, "interview-no@fsp.ru")
    url = f"{API}/assessments/attempts/{attempt['id']}/interview"
    await client.get(url, headers=bearer(token))

    answered = await client.post(url, headers=bearer(token), json={"answers": ["не знаю", ""]})

    assert answered.json()["result"] | {"marks": None} == {
        "score": 10.0,
        "passScore": 60,
        "passed": False,
        "summary": "Итог",
        "marks": None,
    }
    status = (await client.get(f"{API}/assessments/me", headers=bearer(token))).json()
    assert status["status"] == "failed"
    (track,) = status["tracks"]
    assert (track["grade"], track["nextAttemptAt"] is not None) == (None, True)
