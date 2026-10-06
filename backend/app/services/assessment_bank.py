"""Task bank and test templates.

One service for both authors: admins manage the platform bank (`owner_id=None`), an employer
manages only their own rows. A row of another owner answers 404, so its existence is not revealed.
"""

import asyncio
import uuid
from collections.abc import Sequence

from app.core.errors import AppError, NotFoundError
from app.models import AssessmentTask, AssessmentTest, TaskKind
from app.repositories.assessment import AssessmentRepository
from app.schemas.assessment import (
    FixedComposition,
    GroupCheck,
    TaskCheck,
    TaskRead,
    TaskWrite,
    TestRead,
    TestWrite,
)
from app.schemas.common import Page
from app.services.categories import SPECIALIZATIONS
from app.services.code_runner import CodeRunner
from app.services.task_kinds import REGISTRY, spec_of
from app.services.task_kinds.code import CodeKind, judge


def task_write(task: AssessmentTask) -> TaskWrite:
    """The task as its author wrote it: the format of the editor and of export files."""
    return TaskWrite(
        kind=task.kind,
        difficulty=task.difficulty,
        specializations=list(task.specializations),
        topic=task.topic,
        title=task.title,
        statement=task.statement,
        payload=task.payload,
        is_active=task.is_active,
    )


def task_read(task: AssessmentTask) -> TaskRead:
    return TaskRead(
        **task_write(task).model_dump(),
        id=task.id,
        platform=task.owner_id is None,
        created_at=task.created_at,
    )


def test_read(test: AssessmentTest) -> TestRead:
    return TestRead.model_validate(
        {
            "id": test.id,
            "platform": test.owner_id is None,
            "created_at": test.created_at,
            "title": test.title,
            "grade": test.grade,
            "specialization": test.specialization,
            "duration_minutes": test.duration_minutes,
            "pass_score": test.pass_score,
            "quiz_weight": test.quiz_weight,
            "composition": test.composition,
            "retry_days": test.retry_days,
            "grade_change_days": test.grade_change_days,
            "recommend_score": test.recommend_score,
            "is_active": test.is_active,
        }
    )


class AssessmentBankService:
    def __init__(self, repository: AssessmentRepository, runner: CodeRunner) -> None:
        self._repository = repository
        self._runner = runner

    # ── Tasks ─────────────────────────────────────────────────────────────────────────────

    async def list_tasks(
        self,
        owner_id: uuid.UUID | None,
        *,
        kind: TaskKind | None,
        search: str | None,
        page: int,
        per_page: int,
    ) -> Page[TaskRead]:
        tasks, total = await self._repository.list_tasks(
            owner_id, kind=kind, search=search, limit=per_page, offset=(page - 1) * per_page
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

    async def export_tasks(self, owner_id: uuid.UUID | None) -> list[TaskWrite]:
        """The whole bank of the author, grouped by kind and topic to read well as a file."""
        tasks, _ = await self._repository.list_tasks(owner_id)
        ordered = sorted(tasks, key=lambda task: (task.kind.value, task.topic, task.title))
        return [task_write(task) for task in ordered]

    async def import_tasks(self, owner_id: uuid.UUID | None, items: Sequence[TaskWrite]) -> int:
        """Adds every task or none: the first bad one stops the import and names itself."""
        for number, data in enumerate(items, start=1):
            task = AssessmentTask(owner_id=owner_id)
            try:
                _fill_task(task, data)
            except AppError as exc:
                raise AppError(
                    f"Задача №{number} («{data.title}»): {exc.message}", details=exc.details
                ) from exc
            await self._repository.add(task)
        return len(items)

    async def check_task(self, owner_id: uuid.UUID | None, task_id: uuid.UUID) -> TaskCheck:
        """Runs the author's reference solution against every group, hidden ones included."""
        task = await self._task(owner_id, task_id)
        spec = spec_of(task)
        if not isinstance(spec, CodeKind):
            raise AppError("Проверка эталоном доступна только для задач на код")
        payload = spec.payload(task)
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
        platform_only = (
            data.grade,
            data.specialization,
            data.retry_days,
            data.grade_change_days,
            data.recommend_score,
        )
        if owner_id is not None and (
            any(value is not None for value in platform_only)
            or not isinstance(composition, FixedComposition)
        ):
            raise AppError("Тест компании составляется из своих задач и не привязан к грейду")
        if data.specialization is not None and (
            data.grade is None or data.specialization not in SPECIALIZATIONS
        ):
            raise AppError("Специализация теста: одна из справочника и только вместе с грейдом")
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
        test.specialization = data.specialization
        test.duration_minutes = data.duration_minutes
        test.pass_score = data.pass_score
        test.quiz_weight = data.quiz_weight
        test.composition = composition.model_dump(mode="json")
        test.retry_days = data.retry_days
        test.grade_change_days = data.grade_change_days
        test.recommend_score = data.recommend_score
        test.is_active = data.is_active


def _fill_task(task: AssessmentTask, data: TaskWrite) -> None:
    unknown = [code for code in data.specializations if code not in SPECIALIZATIONS]
    if unknown:
        raise AppError("Неизвестная специализация", details={"specializations": unknown})
    spec = REGISTRY[data.kind]
    if spec.manual and task.owner_id is None:
        raise AppError("Задания с ручной проверкой доступны только в тестах компаний")
    task.kind = data.kind
    task.payload = data.payload
    # The stored form is the model's own spelling; the wire spelling is rebuilt on read.
    payload = spec.payload(task)
    spec.check(payload)
    task.payload = payload.model_dump(mode="json")
    task.difficulty = data.difficulty
    task.specializations = list(dict.fromkeys(data.specializations))
    task.topic = data.topic
    task.title = data.title
    task.statement = data.statement
    task.is_active = data.is_active
