"""Workflow status of a bank task and how it maps onto the `is_active` flag candidates obey."""

from typing import Final

from app.admin.enums import TaskStatus
from app.admin.models import AdminTaskMeta
from app.models import AssessmentTask

# Where a task may go from each status. A leaked task never comes back: its content is known.
TRANSITIONS: Final[dict[TaskStatus, frozenset[TaskStatus]]] = {
    TaskStatus.DRAFT: frozenset({TaskStatus.ACTIVE, TaskStatus.ARCHIVED}),
    TaskStatus.ACTIVE: frozenset({TaskStatus.LEAKED, TaskStatus.ARCHIVED}),
    TaskStatus.LEAKED: frozenset({TaskStatus.ARCHIVED}),
    TaskStatus.ARCHIVED: frozenset({TaskStatus.ACTIVE}),
}

STATUS_LABELS: Final = {
    TaskStatus.DRAFT: "Черновик",
    TaskStatus.ACTIVE: "Активен",
    TaskStatus.LEAKED: "Утёк",
    TaskStatus.ARCHIVED: "В архиве",
}


def status_of(task: AssessmentTask, meta: AdminTaskMeta | None) -> TaskStatus:
    """A task the admin panel has not touched yet is active or a draft by its flag."""
    if meta is not None:
        return meta.status
    return TaskStatus.ACTIVE if task.is_active else TaskStatus.DRAFT


def can_move(current: TaskStatus, target: TaskStatus) -> bool:
    return target in TRANSITIONS[current]


def delivered(status: TaskStatus) -> bool:
    """Only active tasks are drawn into candidates' tests."""
    return status == TaskStatus.ACTIVE
