"""Task bank and test templates.

One service for both authors: admins manage the platform bank (`owner_id=None`), an employer
manages only their own rows. A row of another owner answers 404, so its existence is not revealed.
"""

import asyncio
import uuid

from app.core.errors import AppError, NotFoundError
from app.models import AssessmentTask, AssessmentTest, TaskKind
from app.repositories.assessment import AssessmentRepository
from app.schemas.assessment import (
    CodePayload,
    FixedComposition,
    GroupCheck,
    QuizPayload,
    TaskCheck,
    TaskRead,
    TaskWrite,
    TestRead,
    TestWrite,
    Verdict,
)
from app.schemas.common import Page
from app.services.categories import SPECIALIZATIONS
from app.services.code_runner import COMPILERS, CodeRunner, Execution


def quiz_payload(task: AssessmentTask) -> QuizPayload:
    return QuizPayload.model_validate(task.payload)


def code_payload(task: AssessmentTask) -> CodePayload:
    return CodePayload.model_validate(task.payload)


def allowed_languages(payload: CodePayload) -> list[str]:
    """Compiler ids a candidate may pick, in the order of the language menu."""
    return [
        language for language in COMPILERS if not payload.languages or language in payload.languages
    ]


def normalize_output(text: str) -> str:
    """Trailing spaces and blank lines around the output never decide a verdict."""
    lines = text.replace("\r\n", "\n").strip().split("\n")
    return "\n".join(line.rstrip() for line in lines)


def judge(execution: Execution, expected: str, time_limit: float) -> Verdict:
    if execution.killed or (execution.time is not None and execution.time > time_limit):
        return "time_limit"
    if not execution.ok:
        return "runtime_error"
    if normalize_output(execution.output) == normalize_output(expected):
        return "ok"
    return "wrong_answer"


def task_read(task: AssessmentTask) -> TaskRead:
    return TaskRead(
        id=task.id,
        platform=task.owner_id is None,
        created_at=task.created_at,
        kind=task.kind,
        difficulty=task.difficulty,
        specializations=list(task.specializations),
        topic=task.topic,
        title=task.title,
        statement=task.statement,
        quiz=quiz_payload(task) if task.kind == TaskKind.QUIZ else None,
        code=code_payload(task) if task.kind == TaskKind.CODE else None,
        is_active=task.is_active,
    )


def test_read(test: AssessmentTest) -> TestRead:
    return TestRead.model_validate(
        {
            "id": test.id,
            "platform": test.owner_id is None,
            "created_at": test.created_at,
            "title": test.title,
            "grade": test.grade,
            "duration_minutes": test.duration_minutes,
            "pass_score": test.pass_score,
            "quiz_weight": test.quiz_weight,
            "composition": test.composition,
            "is_active": test.is_active,
        }
    )


class AssessmentBankService:
    def __init__(self, repository: AssessmentRepository, runner: CodeRunner) -> None:
        self._repository = repository
        self._runner = runner

    # ── Tasks ─────────────────────────────────────────────────────────────────────────────

    async def list_tasks(
        self, owner_id: uuid.UUID | None, *, kind: TaskKind | None, page: int, per_page: int
    ) -> Page[TaskRead]:
        tasks, total = await self._repository.list_tasks(
            owner_id, kind=kind, limit=per_page, offset=(page - 1) * per_page
        )
        return Page[TaskRead].build(
            [task_read(task) for task in tasks], total=total, page=page, per_page=per_page
        )

    async def create_task(self, owner_id: uuid.UUID | None, data: TaskWrite) -> TaskRead:
        task = AssessmentTask(owner_id=owner_id)
        _fill_task(task, data)
        return task_read(await self._repository.add(task))

    async def update_task(
        self, owner_id: uuid.UUID | None, task_id: uuid.UUID, data: TaskWrite
    ) -> TaskRead:
        task = await self._task(owner_id, task_id)
        _fill_task(task, data)
        return task_read(await self._repository.add(task))

    async def delete_task(self, owner_id: uuid.UUID | None, task_id: uuid.UUID) -> None:
        await self._repository.delete(await self._task(owner_id, task_id))

    async def check_task(self, owner_id: uuid.UUID | None, task_id: uuid.UUID) -> TaskCheck:
        """Runs the author's reference solution against every group, hidden ones included."""
        task = await self._task(owner_id, task_id)
        if task.kind != TaskKind.CODE:
            raise AppError("Проверка эталоном доступна только для задач на код")
        payload = code_payload(task)
        if payload.reference is None:
            raise AppError("У задачи нет эталонного решения")
        reference = payload.reference
        executions = await asyncio.gather(
            *(
                self._runner.run(
                    compiler=reference.language, code=reference.code, stdin=group.input
                )
                for group in payload.groups
            )
        )
        groups = [
            GroupCheck(
                hidden=group.hidden,
                verdict=judge(execution, group.expected, payload.time_limit),
                output=execution.output,
                error=execution.error,
                time=execution.time,
            )
            for group, execution in zip(payload.groups, executions, strict=True)
        ]
        return TaskCheck(ok=all(group.verdict == "ok" for group in groups), groups=groups)

    async def _task(self, owner_id: uuid.UUID | None, task_id: uuid.UUID) -> AssessmentTask:
        task = await self._repository.get_task(task_id)
        if task is None or task.owner_id != owner_id:
            raise NotFoundError("Задача не найдена")
        return task

    # ── Tests ─────────────────────────────────────────────────────────────────────────────

    async def list_tests(self, owner_id: uuid.UUID | None) -> list[TestRead]:
        return [test_read(test) for test in await self._repository.list_tests(owner_id)]

    async def create_test(self, owner_id: uuid.UUID | None, data: TestWrite) -> TestRead:
        test = AssessmentTest(owner_id=owner_id)
        await self._fill_test(test, owner_id, data)
        return test_read(await self._repository.add(test))

    async def update_test(
        self, owner_id: uuid.UUID | None, test_id: uuid.UUID, data: TestWrite
    ) -> TestRead:
        test = await self._test(owner_id, test_id)
        await self._fill_test(test, owner_id, data)
        return test_read(await self._repository.add(test))

    async def delete_test(self, owner_id: uuid.UUID | None, test_id: uuid.UUID) -> None:
        await self._repository.delete(await self._test(owner_id, test_id))

    async def _test(self, owner_id: uuid.UUID | None, test_id: uuid.UUID) -> AssessmentTest:
        test = await self._repository.get_test(test_id)
        if test is None or test.owner_id != owner_id:
            raise NotFoundError("Тест не найден")
        return test

    async def _fill_test(
        self, test: AssessmentTest, owner_id: uuid.UUID | None, data: TestWrite
    ) -> None:
        composition = data.composition
        # Rules draw from the platform bank and a grade confirms a platform category:
        # neither belongs to an employer's own test.
        if owner_id is not None and (
            data.grade is not None or not isinstance(composition, FixedComposition)
        ):
            raise AppError("Тест компании составляется из своих задач и не привязан к грейду")
        if isinstance(composition, FixedComposition):
            tasks = await self._repository.tasks_by_ids(composition.task_ids)
            foreign = [
                str(task_id)
                for task_id in composition.task_ids
                if task_id not in tasks or tasks[task_id].owner_id != owner_id
            ]
            if foreign:
                raise AppError("В тесте есть недоступные задачи", details={"taskIds": foreign})
        test.title = data.title
        test.grade = data.grade
        test.duration_minutes = data.duration_minutes
        test.pass_score = data.pass_score
        test.quiz_weight = data.quiz_weight
        test.composition = composition.model_dump(mode="json")
        test.is_active = data.is_active


def _fill_task(task: AssessmentTask, data: TaskWrite) -> None:
    unknown = [code for code in data.specializations if code not in SPECIALIZATIONS]
    if unknown:
        raise AppError("Неизвестная специализация", details={"specializations": unknown})
    payload = data.quiz or data.code
    if isinstance(payload, CodePayload):
        languages = [
            *payload.languages,
            *([payload.reference.language] if payload.reference else []),
        ]
        unsupported = [language for language in languages if language not in COMPILERS]
        if unsupported:
            raise AppError("Неподдерживаемый язык", details={"languages": unsupported})
        if payload.reference and payload.reference.language not in allowed_languages(payload):
            raise AppError("Язык эталонного решения не разрешён в задаче")
    if payload is None:  # pragma: no cover - TaskWrite guarantees one of the two
        raise AppError()
    task.kind = data.kind
    task.difficulty = data.difficulty
    task.specializations = list(dict.fromkeys(data.specializations))
    task.topic = data.topic
    task.title = data.title
    task.statement = data.statement
    task.payload = payload.model_dump(mode="json")
    task.is_active = data.is_active
