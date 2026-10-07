"""The platform task bank as the admin panel manages it.

Tasks stay in `assessment_tasks` and are validated by the bank's own service; the panel adds a
workflow status (mirrored into `is_active`, which decides what candidates get), an 11-level
grade, variables of the statement, a time limit and the history of every change.
"""

import re
import secrets
import uuid
from typing import Any, Final

from pydantic import ValidationError
from sqlalchemy import ColumnElement, String, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.audit import AuditLog, diff
from app.admin.dictionaries import GRADE_CODES
from app.admin.enums import TaskStatus
from app.admin.models import AdminTaskMeta
from app.admin.schemas import (
    AdminTaskCreate,
    AdminTaskDetail,
    AdminTaskRow,
    AdminTaskWrite,
    PreviewRequest,
    PreviewVariant,
    StatusChange,
    TaskVariable,
)
from app.admin.tasks_status import TRANSITIONS, can_move, delivered, status_of
from app.core.errors import AppError, ConflictError, NotFoundError
from app.models import AssessmentAttempt, AssessmentTask, TaskKind, User
from app.schemas.assessment import TaskWrite
from app.schemas.common import Page
from app.services.assessment_bank import AssessmentBankService

_random = secrets.SystemRandom()
_PLACEHOLDER: Final = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
ADMIN_KINDS: Final = (TaskKind.QUIZ, TaskKind.CODE)


def status_column() -> ColumnElement[Any]:
    """The workflow status in SQL, with the same fallback as `status_of`."""
    return func.coalesce(
        AdminTaskMeta.status,
        case(
            (AssessmentTask.is_active.is_(True), TaskStatus.ACTIVE.value),
            else_=TaskStatus.DRAFT.value,
        ),
    )


def _row(task: AssessmentTask, meta: AdminTaskMeta | None) -> AdminTaskRow:
    return AdminTaskRow(
        id=task.id,
        title=task.title,
        kind=task.kind,
        specializations=list(task.specializations),
        grade=meta.grade if meta else None,
        skill=task.topic,
        difficulty=task.difficulty,
        status=status_of(task, meta),
        updated_at=max(task.updated_at, meta.updated_at) if meta else task.updated_at,
    )


def _editable(task: AssessmentTask, meta: AdminTaskMeta | None) -> dict[str, Any]:
    """What an edit can change: compared before and after to journal the difference."""
    return {
        "kind": task.kind.value,
        "title": task.title,
        "statement": task.statement,
        "specializations": list(task.specializations),
        "skill": task.topic,
        "difficulty": task.difficulty.value,
        "payload": task.payload,
        "grade": meta.grade if meta else None,
        "variables": list(meta.variables) if meta else [],
        "timeLimitMinutes": meta.time_limit_minutes if meta else None,
    }


def substitute(text: str, values: dict[str, float]) -> str:
    """`{name}` → the value; unknown placeholders stay as they are."""

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in values:
            return match.group(0)
        value = values[name]
        return str(int(value)) if float(value).is_integer() else f"{value:g}"

    return _PLACEHOLDER.sub(replace, text)


def draw_values(variables: list[TaskVariable]) -> dict[str, float]:
    """A random value of every variable within its range, on its step."""
    values: dict[str, float] = {}
    for variable in variables:
        steps = int((variable.max - variable.min) // variable.step)
        value = variable.min + variable.step * _random.randint(0, max(steps, 0))
        values[variable.name] = round(value, 6)
    return values


class AdminBankService:
    def __init__(self, session: AsyncSession, bank: AssessmentBankService) -> None:
        self._session = session
        self._bank = bank
        self._audit = AuditLog(session)

    # ── Reading ───────────────────────────────────────────────────────────────────────────

    def _filtered(
        self,
        *,
        specialization: str | None,
        grade: str | None,
        skill: str | None,
        kind: TaskKind | None,
        status: TaskStatus | None,
        search: str | None,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = [
            AssessmentTask.owner_id.is_(None),
            AssessmentTask.kind.in_(ADMIN_KINDS),
        ]
        if specialization:
            # A JSON list of codes: the quoted code is a substring of its text in both databases.
            conditions.append(
                cast(AssessmentTask.specializations, String).like(f'%"{specialization}"%')
            )
        if grade:
            conditions.append(AdminTaskMeta.grade == grade)
        if skill:
            conditions.append(AssessmentTask.topic == skill)
        if kind:
            conditions.append(AssessmentTask.kind == kind)
        if status:
            conditions.append(status_column() == status.value)
        if search:
            conditions.append(AssessmentTask.title.ilike(f"%{search.strip()}%"))
        return conditions

    async def page(
        self,
        *,
        specialization: str | None = None,
        grade: str | None = None,
        skill: str | None = None,
        kind: TaskKind | None = None,
        status: TaskStatus | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Page[AdminTaskRow]:
        conditions = self._filtered(
            specialization=specialization,
            grade=grade,
            skill=skill,
            kind=kind,
            status=status,
            search=search,
        )
        base = select(AssessmentTask, AdminTaskMeta).outerjoin(
            AdminTaskMeta, AdminTaskMeta.task_id == AssessmentTask.id
        )
        total = await self._session.scalar(
            select(func.count())
            .select_from(AssessmentTask)
            .outerjoin(AdminTaskMeta, AdminTaskMeta.task_id == AssessmentTask.id)
            .where(*conditions)
        )
        rows = (
            await self._session.execute(
                base.where(*conditions)
                .order_by(AssessmentTask.created_at.desc(), AssessmentTask.id)
                .limit(per_page)
                .offset((page - 1) * per_page)
            )
        ).all()
        return Page[AdminTaskRow].build(
            [_row(task, meta) for task, meta in rows],
            total=total or 0,
            page=page,
            per_page=per_page,
        )

    async def export_rows(self, **filters: Any) -> list[AdminTaskRow]:
        conditions = self._filtered(**filters)
        rows = (
            await self._session.execute(
                select(AssessmentTask, AdminTaskMeta)
                .outerjoin(AdminTaskMeta, AdminTaskMeta.task_id == AssessmentTask.id)
                .where(*conditions)
                .order_by(AssessmentTask.created_at.desc(), AssessmentTask.id)
            )
        ).all()
        return [_row(task, meta) for task, meta in rows]

    async def skills(self) -> list[str]:
        """Topics already used by platform tasks: suggestions for the «навык» field."""
        result = await self._session.scalars(
            select(AssessmentTask.topic)
            .where(AssessmentTask.owner_id.is_(None))
            .distinct()
            .order_by(AssessmentTask.topic)
        )
        return list(result)

    async def detail(self, task_id: uuid.UUID) -> AdminTaskDetail:
        task, meta = await self._load(task_id)
        attempts = await self.attempts_with(task_id)
        status = status_of(task, meta)
        return AdminTaskDetail(
            **_row(task, meta).model_dump(),
            statement=task.statement,
            variables=[
                TaskVariable.model_validate(item) for item in (meta.variables if meta else [])
            ],
            time_limit_minutes=meta.time_limit_minutes if meta else None,
            payload=task.payload,
            created_at=task.created_at,
            attempts=attempts,
            can_delete=status == TaskStatus.DRAFT and attempts == 0,
            allowed_statuses=sorted(TRANSITIONS[status], key=list(TaskStatus).index),
        )

    async def attempts_with(self, task_id: uuid.UUID) -> int:
        """Attempts whose variant held the task (looked up in the JSON list of ids)."""
        count = await self._session.scalar(
            select(func.count())
            .select_from(AssessmentAttempt)
            .where(cast(AssessmentAttempt.task_ids, String).like(f"%{task_id}%"))
        )
        return count or 0

    # ── Writing ───────────────────────────────────────────────────────────────────────────

    async def create(self, actor: User, data: AdminTaskCreate) -> AdminTaskDetail:
        _check_grade(data.grade)
        created = await self._bank.create_task(None, _task_write(data, delivered(data.status)))
        task, _ = await self._load(created.id)
        meta = AdminTaskMeta(task_id=task.id, status=data.status)
        _fill_meta(meta, data)
        self._session.add(meta)
        await self._session.flush()
        await self._audit.record(
            actor,
            "task",
            task.id,
            "create",
            diff({}, {**_editable(task, meta), "status": data.status.value}),
        )
        return await self.detail(task.id)

    async def update(
        self, actor: User, task_id: uuid.UUID, data: AdminTaskWrite
    ) -> AdminTaskDetail:
        _check_grade(data.grade)
        task, meta = await self._load(task_id)
        before = _editable(task, meta)
        status = status_of(task, meta)
        await self._bank.update_task(None, task_id, _task_write(data, delivered(status)))
        if meta is None:
            meta = AdminTaskMeta(task_id=task.id, status=status)
            self._session.add(meta)
        _fill_meta(meta, data)
        await self._session.flush()
        changes = diff(before, _editable(task, meta))
        if changes:
            await self._audit.record(actor, "task", task.id, "update", changes)
        return await self.detail(task.id)

    async def change_status(
        self, actor: User, task_id: uuid.UUID, change: StatusChange
    ) -> AdminTaskDetail:
        task, meta = await self._load(task_id)
        current = status_of(task, meta)
        if change.status == current:
            return await self.detail(task_id)
        if not can_move(current, change.status):
            raise ConflictError("Такой переход статуса недоступен")
        if meta is None:
            meta = AdminTaskMeta(task_id=task.id, status=current, variables=[])
            self._session.add(meta)
        meta.status = change.status
        # What candidates get is decided by this flag: only active tasks are drawn.
        task.is_active = delivered(change.status)
        await self._session.flush()
        await self._audit.record(
            actor,
            "task",
            task.id,
            "status",
            {"status": [current.value, change.status.value]},
            reason=change.reason,
        )
        return await self.detail(task_id)

    async def delete(self, actor: User, task_id: uuid.UUID) -> None:
        task, meta = await self._load(task_id)
        if status_of(task, meta) != TaskStatus.DRAFT:
            raise ConflictError("Удалить можно только черновик")
        if await self.attempts_with(task_id):
            raise ConflictError(
                "Задание уже было в попытках кандидатов: его можно только архивировать"
            )
        title = task.title
        if meta is not None:
            await self._session.delete(meta)
            await self._session.flush()
        await self._bank.delete_task(None, task_id)
        await self._audit.record(actor, "task", task_id, "delete", {"title": [title, None]})

    def preview(self, request: PreviewRequest) -> list[PreviewVariant]:
        variants = []
        for _ in range(request.count):
            values = draw_values(request.variables)
            variants.append(
                PreviewVariant(
                    values=values,
                    statement=substitute(request.statement, values),
                    options=[substitute(option, values) for option in request.options],
                )
            )
        return variants

    async def _load(self, task_id: uuid.UUID) -> tuple[AssessmentTask, AdminTaskMeta | None]:
        # Re-read: updated_at is set by the database on update and expires after a flush.
        task = await self._session.get(AssessmentTask, task_id, populate_existing=True)
        if task is None or task.owner_id is not None or task.kind not in ADMIN_KINDS:
            raise NotFoundError("Задание не найдено")
        return task, await self._session.get(AdminTaskMeta, task_id, populate_existing=True)


def _check_grade(grade: str | None) -> None:
    if grade is not None and grade not in GRADE_CODES:
        raise AppError("Неизвестный грейд")


def _task_write(data: AdminTaskWrite, is_active: bool) -> TaskWrite:
    try:
        return TaskWrite(
            kind=data.kind,
            difficulty=data.difficulty,
            specializations=data.specializations,
            topic=data.skill,
            title=data.title,
            statement=data.statement,
            payload=data.payload,
            is_active=is_active,
        )
    except ValidationError as exc:
        problems = "; ".join(str(error["msg"]) for error in exc.errors())
        raise AppError(f"Содержимое задания: {problems}") from exc


def _fill_meta(meta: AdminTaskMeta, data: AdminTaskWrite) -> None:
    meta.grade = data.grade
    meta.variables = [variable.model_dump(mode="json") for variable in data.variables]
    meta.time_limit_minutes = data.time_limit_minutes
