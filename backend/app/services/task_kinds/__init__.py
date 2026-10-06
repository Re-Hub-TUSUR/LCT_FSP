"""Registry of task kinds.

To add a kind: a `TaskKind` member, its payload model in `schemas.assessment.PAYLOAD_MODELS`,
a `TaskKindSpec` subclass here — and a view plus an editor on the frontend.
"""

from typing import Any

from app.models import TaskKind
from app.services.task_kinds.base import Stored, Task, TaskKindSpec, TaskSnapshot
from app.services.task_kinds.code import CodeKind
from app.services.task_kinds.open import OpenKind
from app.services.task_kinds.quiz import QuizKind

REGISTRY: dict[TaskKind, TaskKindSpec[Any]] = {
    spec.kind: spec for spec in (QuizKind(), CodeKind(), OpenKind())
}


def spec_of(task: Task) -> TaskKindSpec[Any]:
    return REGISTRY[task.kind]


__all__ = ["REGISTRY", "Stored", "Task", "TaskKindSpec", "TaskSnapshot", "spec_of"]
