"""Starter task bank and grade test templates of the platform.

`uv run python -m app.seed.assessment` loads them into the configured database. Unlike the demo
dataset this is real content: the command is safe in production and runs on every start of the
compose stand. It only adds rows that are missing (ids derive from the files), so tasks made in the
admin panel and admin edits of starter rows stay intact. Switch a starter task off instead of
deleting it — a deleted one comes back on the next run.

Files in `data/assessment/`:
- `quiz.json` and `quiz/*.json` — rows `[specialization | null, topic, "e" | "m" | "h", question,
  correct, wrong…]`; the first option is the correct one (options are shuffled for every attempt);
- `code.json` and `code/*.json` — stdin/stdout tasks with test groups and a reference solution;
  the files of the folder are built by `python -m app.seed.code_bank`, do not edit them by hand;
- `tests.json` — one template per grade: duration and composition rules.

The id of a question derives from its text and the id of a code task from its key: rewording a
question adds a new row and leaves the old one in databases that already have it.

Difficulty is what ties a task to a grade (the templates pick it): an easy question asks to
recognise one basic notion, a medium one to apply it to a typical situation, a hard one to weigh
trade-offs, diagnose a failure or know how a thing works inside.
"""

import asyncio
import json
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_engine, get_sessionmaker
from app.models import AssessmentTask, AssessmentTest, Grade, TaskDifficulty, TaskKind
from app.schemas.assessment import CodePayload, QuizPayload, RulesComposition

DATA_DIR: Final = Path(__file__).parent / "data" / "assessment"
NAMESPACE: Final = uuid.UUID("b3a0f6f2-7d0e-4a57-9d55-0c1f4a6a2e11")
DIFFICULTY: Final = {"e": TaskDifficulty.EASY, "m": TaskDifficulty.MEDIUM, "h": TaskDifficulty.HARD}
# Bumped when the compositions in `tests.json` change: templates are only ever added, so a new
# version gets new ids and the previous ones are switched off.
TEMPLATE_VERSION: Final = 2


@dataclass(frozen=True, slots=True)
class BankSummary:
    quiz: int
    code: int
    tests: int


def _id(kind: str, key: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"{kind}:{key}")


def _template_id(grade: str, version: int) -> uuid.UUID:
    return _id("test", grade if version == 1 else f"{grade}:{version}")


def _read(path: Path) -> list[Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        msg = f"{path.name}: expected a list"
        raise TypeError(msg)
    return data


def _rows(stem: str) -> list[Any]:
    """Rows of `<stem>.json` followed by every file of the `<stem>/` folder."""
    files = [DATA_DIR / f"{stem}.json", *sorted((DATA_DIR / stem).glob("*.json"))]
    return [row for path in files for row in _read(path)]


def quiz_tasks() -> list[AssessmentTask]:
    tasks = []
    for specialization, topic, difficulty, question, *options in _rows("quiz"):
        payload = QuizPayload(options=options, correct=[0])
        tasks.append(
            AssessmentTask(
                id=_id("quiz", question),
                kind=TaskKind.QUIZ,
                difficulty=DIFFICULTY[difficulty],
                specializations=[specialization] if specialization else [],
                topic=topic,
                title=question,
                statement=question,
                payload=payload.model_dump(mode="json"),
            )
        )
    return tasks


def code_tasks() -> list[AssessmentTask]:
    tasks = []
    for item in _rows("code"):
        payload = CodePayload.model_validate(
            {key: item[key] for key in ("time_limit", "groups", "reference")}
        )
        tasks.append(
            AssessmentTask(
                id=_id("code", item["key"]),
                kind=TaskKind.CODE,
                difficulty=TaskDifficulty(item["difficulty"]),
                specializations=item["specializations"],
                topic=item["topic"],
                title=item["title"],
                statement=item["statement"],
                payload=payload.model_dump(mode="json"),
            )
        )
    return tasks


def grade_tests() -> list[AssessmentTest]:
    tests = []
    for item in _read(DATA_DIR / "tests.json"):
        composition = RulesComposition.model_validate({"rules": item["rules"]})
        tests.append(
            AssessmentTest(
                id=_template_id(item["grade"], TEMPLATE_VERSION),
                title=item["title"],
                grade=Grade(item["grade"]),
                duration_minutes=item["duration_minutes"],
                pass_score=item.get("pass_score", 60),
                quiz_weight=item.get("quiz_weight", 40),
                composition=composition.model_dump(mode="json"),
            )
        )
    return tests


async def seed_assessment_bank(session: AsyncSession) -> BankSummary:
    """Adds the starter rows that are not in the database yet. The caller commits."""
    quiz, code, tests = quiz_tasks(), code_tasks(), grade_tests()
    rows: list[AssessmentTask | AssessmentTest] = [*quiz, *code, *tests]
    for row in rows:
        if await session.get(type(row), row.id) is None:
            session.add(row)
    for grade in Grade:
        for version in range(1, TEMPLATE_VERSION):
            outdated = await session.get(AssessmentTest, _template_id(grade, version))
            if outdated is not None:
                outdated.is_active = False
    await session.flush()
    return BankSummary(quiz=len(quiz), code=len(code), tests=len(tests))


async def _main() -> BankSummary:
    try:
        async with get_sessionmaker()() as session:
            summary = await seed_assessment_bank(session)
            await session.commit()
    finally:
        await get_engine().dispose()
    return summary


if __name__ == "__main__":
    result = asyncio.run(_main())
    print(
        f"Task bank loaded: {result.quiz} questions, {result.code} code tasks, "
        f"{result.tests} grade tests."
    )
    sys.exit(0)
