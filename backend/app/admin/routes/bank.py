import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.admin.audit import AuditLog
from app.admin.csv_export import csv_response
from app.admin.dependencies import AdminBankDep
from app.admin.enums import TaskStatus
from app.admin.schemas import (
    AdminTaskCreate,
    AdminTaskDetail,
    AdminTaskRow,
    AdminTaskWrite,
    AuditEntryRead,
    PreviewRequest,
    PreviewVariant,
    StatusChange,
)
from app.admin.services.employers import audit_read
from app.admin.tasks_status import STATUS_LABELS
from app.dependencies.auth import AdminUser
from app.dependencies.common import SessionDep
from app.models import TaskKind
from app.schemas.common import Page

router = APIRouter(prefix="/bank")

PER_PAGE = 50
Search = Annotated[str | None, Query(max_length=200, description="Название")]
Code = Annotated[str | None, Query(max_length=64)]


@router.get("/tasks", summary="Platform tasks with filters, 50 per page")
async def list_tasks(
    *,
    _: AdminUser,
    service: AdminBankDep,
    page: Annotated[int, Query(ge=1)] = 1,
    specialization: Code = None,
    grade: Code = None,
    skill: Code = None,
    kind: TaskKind | None = None,
    task_status: Annotated[TaskStatus | None, Query(alias="status")] = None,
    q: Search = None,
) -> Page[AdminTaskRow]:
    return await service.page(
        specialization=specialization,
        grade=grade,
        skill=skill,
        kind=kind,
        status=task_status,
        search=q,
        page=page,
        per_page=PER_PAGE,
    )


@router.get("/tasks/export.csv", summary="The filtered task list as CSV")
async def export_tasks(
    *,
    _: AdminUser,
    service: AdminBankDep,
    specialization: Code = None,
    grade: Code = None,
    skill: Code = None,
    kind: TaskKind | None = None,
    task_status: Annotated[TaskStatus | None, Query(alias="status")] = None,
    q: Search = None,
) -> Response:
    rows = await service.export_rows(
        specialization=specialization,
        grade=grade,
        skill=skill,
        kind=kind,
        status=task_status,
        search=q,
    )
    return csv_response(
        "task-bank.csv",
        [
            "ID",
            "Название",
            "Тип",
            "Специализации",
            "Грейд",
            "Навык",
            "Сложность",
            "Статус",
            "Изменено",
        ],
        (
            [
                row.id,
                row.title,
                "Тест" if row.kind == TaskKind.QUIZ else "Код",
                row.specializations,
                row.grade,
                row.skill,
                row.difficulty.value,
                STATUS_LABELS[row.status],
                row.updated_at.isoformat(),
            ]
            for row in rows
        ),
    )


@router.get("/skills", summary="Skills (topics) already used in the platform bank")
async def list_skills(_: AdminUser, service: AdminBankDep) -> list[str]:
    return await service.skills()


@router.post("/preview", summary="Statement with random values of its variables, side by side")
async def preview(
    _: AdminUser, data: PreviewRequest, service: AdminBankDep
) -> list[PreviewVariant]:
    return service.preview(data)


@router.post("/tasks", status_code=status.HTTP_201_CREATED, summary="Add a task")
async def create_task(
    user: AdminUser, data: AdminTaskCreate, service: AdminBankDep
) -> AdminTaskDetail:
    return await service.create(user, data)


@router.get("/tasks/{task_id}", summary="A task with its workflow data")
async def read_task(task_id: uuid.UUID, _: AdminUser, service: AdminBankDep) -> AdminTaskDetail:
    return await service.detail(task_id)


@router.put("/tasks/{task_id}", summary="Edit a task")
async def update_task(
    task_id: uuid.UUID, user: AdminUser, data: AdminTaskWrite, service: AdminBankDep
) -> AdminTaskDetail:
    return await service.update(user, task_id, data)


@router.post(
    "/tasks/{task_id}/status", summary="Move a task along Draft → Active → Leaked/Archived"
)
async def change_status(
    task_id: uuid.UUID, user: AdminUser, data: StatusChange, service: AdminBankDep
) -> AdminTaskDetail:
    return await service.change_status(user, task_id, data)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a draft that never was in an attempt",
)
async def delete_task(task_id: uuid.UUID, user: AdminUser, service: AdminBankDep) -> None:
    await service.delete(user, task_id)


@router.get("/tasks/{task_id}/history", summary="Who changed the task, when and what")
async def task_history(
    task_id: uuid.UUID,
    _: AdminUser,
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
) -> Page[AuditEntryRead]:
    entries, total = await AuditLog(session).page(
        entity="task", entity_id=str(task_id), limit=PER_PAGE, offset=(page - 1) * PER_PAGE
    )
    return Page[AuditEntryRead].build(
        [audit_read(entry, email) for entry, email in entries],
        total=total,
        page=page,
        per_page=PER_PAGE,
    )
