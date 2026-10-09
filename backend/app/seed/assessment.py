"""Starter task bank and grade test templates of the platform.

`uv run python -m app.seed.assessment` loads them into the configured database. Unlike the demo
dataset this is real content: the command is safe in production and runs on every start of the
compose stand. It only adds rows that are missing (ids derive from the files), so tasks made in the
admin panel and admin edits of starter rows stay intact. Switch a starter task off instead of
deleting it — a deleted one comes back on the next run.

Files in `data/assessment/`:
- `quiz.json` and `quiz/*.json` — rows `[specialization | null, topic, "e" | "m" | "h", question,
  correct, wrong…]`; the first option is the correct one (options are shuffled for every attempt)
  and any number of wrong ones may follow. A list in place of `correct` makes a question with
  several right options: `[…, question, ["right", "right too"], "wrong", "wrong", "wrong"]`;
- `code.json` and `code/*.json` — stdin/stdout tasks with test groups and a reference solution,
  optionally a `starter` (compiler id → the code to fix) and a `weight` of a hidden group;
  the files of the folder are built by `python -m app.seed.code_bank`, do not edit them by hand;
- `tests.json` — one template per grade: duration and composition rules; optional `pass_score`,
  `quiz_weight`, `recommend_score`, `retry_days`, `grade_change_days` (the defaults apply when
  absent).

The id of a question derives from its text and the id of a code task from its key: rewording a
question adds a new row and leaves the old one in databases that already have it.

A starter row that nobody edited follows the files: its difficulty, topic, specializations,
statement and payload (options, test groups) are brought up to date on every run. A row edited in
the admin panel stays as it is, and `is_active` is never touched (see `_follows_files`).

Difficulty is what ties a task to a grade (the templates pick it): an easy question asks to
recognise one basic notion, a medium one to apply it to a typical situation, a hard one to weigh
trade-offs, diagnose a failure or know how a thing works inside.
"""

import asyncio
import hashlib
import json
import sys
import uuid
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Final

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_engine, get_sessionmaker
from app.models import AssessmentTask, AssessmentTest, Grade, TaskDifficulty, TaskKind
from app.schemas.assessment import CodePayload, QuizPayload, RulesComposition
from app.services.quiz_lint import MAX_LONGEST_SHARE, longest_share, option_warning

DATA_DIR: Final = Path(__file__).parent / "data" / "assessment"
NAMESPACE: Final = uuid.UUID("b3a0f6f2-7d0e-4a57-9d55-0c1f4a6a2e11")
DIFFICULTY: Final = {"e": TaskDifficulty.EASY, "m": TaskDifficulty.MEDIUM, "h": TaskDifficulty.HARD}
# Bumped when the compositions in `tests.json` change: templates are only ever added, so a new
# version gets new ids and the previous ones are switched off.
TEMPLATE_VERSION: Final = 4


@dataclass(frozen=True, slots=True)
class BankSummary:
    quiz: int
    code: int
    tests: int
    # Starter rows brought up to date with the files.
    updated: int = 0


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
    """The starter questions. A question whose right option gives itself away by its length
    does not load: see `app.services.quiz_lint` for the rule."""
    tasks = []
    rows = _rows("quiz")
    for specialization, topic, difficulty, question, correct, *wrong in rows:
        warning = option_warning(correct, wrong)
        if warning:
            msg = f"{question}: {warning}"
            raise ValueError(msg)
        right = [correct] if isinstance(correct, str) else correct
        payload = QuizPayload(
            options=[*right, *wrong],
            correct=list(range(len(right))),
            multiple=not isinstance(correct, str),
        )
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
    share = longest_share((row[4], row[5:]) for row in rows)
    if share > MAX_LONGEST_SHARE:
        msg = (
            f"Правильный ответ самый длинный в {share:.0%} вопросов, "
            f"допустимо до {MAX_LONGEST_SHARE:.0%}"
        )
        raise ValueError(msg)
    return tasks


def code_tasks() -> list[AssessmentTask]:
    tasks = []
    for item in _rows("code"):
        payload = CodePayload.model_validate(
            {
                key: item[key]
                for key in ("time_limit", "groups", "reference", "starter")
                if key in item
            }
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
                quiz_min=item.get("quiz_min", 0),
                is_beta=item.get("is_beta", False),
                # Absent = the platform defaults from the settings.
                retry_days=item.get("retry_days"),
                grade_change_days=item.get("grade_change_days"),
                recommend_score=item.get("recommend_score"),
                composition=composition.model_dump(mode="json"),
            )
        )
    return tests


def content_hash(task: AssessmentTask) -> str:
    """Fingerprint of what the starter files define for a task."""
    content = [
        TaskKind(task.kind).value,
        TaskDifficulty(task.difficulty).value,
        task.topic,
        sorted(task.specializations),
        task.title,
        task.statement,
        task.payload,
    ]
    text = json.dumps(content, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode()).hexdigest()


def _follows_files(task: AssessmentTask) -> bool:
    """True while nobody has edited the row since the seed wrote it."""
    if task.seed_hash is not None:
        return content_hash(task) == task.seed_hash
    # Written before the hash existed: an untouched row has `updated_at == created_at`.
    return task.updated_at - task.created_at < timedelta(seconds=1)


async def seed_assessment_bank(session: AsyncSession) -> BankSummary:
    """Adds the starter rows that are not in the database yet and brings the untouched ones up
    to date with the files. The caller commits."""
    quiz, code, tests = quiz_tasks(), code_tasks(), grade_tests()
    rows: list[AssessmentTask | AssessmentTest] = [*quiz, *code, *tests]
    updated = 0
    for row in rows:
        existing = await session.get(type(row), row.id)
        if isinstance(row, AssessmentTask):
            row.seed_hash = content_hash(row)
        if existing is None:
            session.add(row)
        elif (
            isinstance(row, AssessmentTask)
            and isinstance(existing, AssessmentTask)
            and _follows_files(existing)
        ):
            if content_hash(existing) != row.seed_hash:
                existing.difficulty = row.difficulty
                existing.topic = row.topic
                existing.specializations = row.specializations
                existing.title = row.title
                existing.statement = row.statement
                existing.payload = row.payload
                updated += 1
            existing.seed_hash = row.seed_hash
    for grade in Grade:
        for version in range(1, TEMPLATE_VERSION):
            outdated = await session.get(AssessmentTest, _template_id(grade, version))
            if outdated is not None:
                outdated.is_active = False
    await session.flush()
    return BankSummary(quiz=len(quiz), code=len(code), tests=len(tests), updated=updated)


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
        f"{result.tests} grade tests; {result.updated} starter tasks brought up to date."
    )
    sys.exit(0)
