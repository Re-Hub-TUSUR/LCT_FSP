"""Task bank endpoints, mounted twice: for admins (platform bank) and for employers (own bank)."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Body, Query, status

from app.dependencies.common import PaginationDep
from app.dependencies.services import AssessmentBankServiceDep
from app.models import TaskKind, User, UserRole
from app.schemas.assessment import (
    MAX_IMPORT_TASKS,
    ImportResult,
    TaskCheck,
    TaskRead,
    TaskWrite,
    TestRead,
    TestWrite,
)
from app.schemas.common import Page


def _owner(user: User) -> uuid.UUID | None:
    return None if user.role == UserRole.ADMIN else user.id


def bank_router(author: Any) -> APIRouter:
    """`author` is the role guard (`AdminUser` or `EmployerUser`) of the mounting router."""
    router = APIRouter()

    @router.get("/assessment-tasks", summary="Tasks of the bank")
    async def list_tasks(
        user: author,
        pagination: PaginationDep,
        service: AssessmentBankServiceDep,
        kind: TaskKind | None = None,
        q: Annotated[str | None, Query(max_length=200, description="Title or topic")] = None,
    ) -> Page[TaskRead]:
        return await service.list_tasks(
            _owner(user), kind=kind, search=q, page=pagination.page, per_page=pagination.per_page
        )

    @router.get(
        "/assessment-tasks/export",
        summary="The whole bank as a JSON list",
        description="Every item has the shape of the task body, so the file imports back as is.",
    )
    async def export_tasks(user: author, service: AssessmentBankServiceDep) -> list[TaskWrite]:
        return await service.export_tasks(_owner(user))

    @router.post(
        "/assessment-tasks/import",
        status_code=status.HTTP_201_CREATED,
        summary="Add tasks from a JSON list: all of them or none",
    )
    async def import_tasks(
        user: author,
        items: Annotated[list[TaskWrite], Body(min_length=1, max_length=MAX_IMPORT_TASKS)],
        service: AssessmentBankServiceDep,
    ) -> ImportResult:
        return ImportResult(created=await service.import_tasks(_owner(user), items))

    @router.post("/assessment-tasks", status_code=status.HTTP_201_CREATED, summary="Add a task")
    async def create_task(
        user: author, data: TaskWrite, service: AssessmentBankServiceDep
    ) -> TaskRead:
        return await service.create_task(_owner(user), data)

    @router.put("/assessment-tasks/{task_id}", summary="Replace a task")
    async def update_task(
        task_id: uuid.UUID, user: author, data: TaskWrite, service: AssessmentBankServiceDep
    ) -> TaskRead:
        return await service.update_task(_owner(user), task_id, data)

    @router.delete(
        "/assessment-tasks/{task_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete a task",
    )
    async def delete_task(
        task_id: uuid.UUID, user: author, service: AssessmentBankServiceDep
    ) -> None:
        await service.delete_task(_owner(user), task_id)

    @router.post(
        "/assessment-tasks/{task_id}/check",
        summary="Run the reference solution against every test group",
    )
    async def check_task(
        task_id: uuid.UUID, user: author, service: AssessmentBankServiceDep
    ) -> TaskCheck:
        return await service.check_task(_owner(user), task_id)

    @router.get("/assessment-tests", summary="Test templates")
    async def list_tests(user: author, service: AssessmentBankServiceDep) -> list[TestRead]:
        return await service.list_tests(_owner(user))

    @router.post("/assessment-tests", status_code=status.HTTP_201_CREATED, summary="Add a test")
    async def create_test(
        user: author, data: TestWrite, service: AssessmentBankServiceDep
    ) -> TestRead:
        return await service.create_test(_owner(user), data)

    @router.put("/assessment-tests/{test_id}", summary="Replace a test")
    async def update_test(
        test_id: uuid.UUID, user: author, data: TestWrite, service: AssessmentBankServiceDep
    ) -> TestRead:
        return await service.update_test(_owner(user), test_id, data)

    @router.delete(
        "/assessment-tests/{test_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete a test",
    )
    async def delete_test(
        test_id: uuid.UUID, user: author, service: AssessmentBankServiceDep
    ) -> None:
        await service.delete_test(_owner(user), test_id)

    return router
