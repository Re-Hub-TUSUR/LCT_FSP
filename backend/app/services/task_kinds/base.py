"""What a task kind has to define. Everything kind-specific lives in the kind's own module:
the bank, the attempt flow and the scoring only talk to this interface."""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Self, cast

from app.models import AssessmentTask, TaskDifficulty, TaskKind
from app.schemas.assessment import PAYLOAD_MODELS
from app.schemas.common import ApiModel
from app.services.code_runner import CodeRunner

# Answers and per-attempt state are stored as JSON.
Stored = dict[str, Any]


@dataclass(frozen=True, slots=True)
class TaskSnapshot:
    """A task as it was when an attempt started. Attempts keep these copies and never look
    into the bank again, so editing or deleting a task cannot change a test already taken."""

    id: uuid.UUID
    kind: TaskKind
    topic: str
    difficulty: TaskDifficulty
    title: str
    statement: str
    payload: dict[str, Any]

    @classmethod
    def of(cls, task: AssessmentTask) -> Self:
        return cls(
            id=task.id,
            kind=task.kind,
            topic=task.topic,
            difficulty=task.difficulty,
            title=task.title,
            statement=task.statement,
            payload=dict(task.payload),
        )

    @classmethod
    def load(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=uuid.UUID(data["id"]),
            kind=TaskKind(data["kind"]),
            topic=data["topic"],
            difficulty=TaskDifficulty(data["difficulty"]),
            title=data["title"],
            statement=data["statement"],
            payload=data["payload"],
        )

    def dump(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "kind": self.kind.value,
            "topic": self.topic,
            "difficulty": self.difficulty.value,
            "title": self.title,
            "statement": self.statement,
            "payload": self.payload,
        }


# A row of the bank or an attempt's copy of it.
Task = AssessmentTask | TaskSnapshot


class TaskKindSpec[P: ApiModel](ABC):
    kind: ClassVar[TaskKind]
    # Group in the score formula: code tasks share `100 - quiz_weight`, the rest `quiz_weight`.
    code_group: ClassVar[bool] = False
    # True: a person grades it, so only an employer's own test may hold it (a grade test
    # must be scored by the platform alone).
    manual: ClassVar[bool] = False

    def payload(self, task: Task) -> P:
        return cast(P, PAYLOAD_MODELS[self.kind].model_validate(task.payload))

    def check(self, payload: P) -> None:  # noqa: B027 - optional hook
        """Rules a schema cannot express. Raises `AppError`."""

    def new_state(self, payload: P) -> Stored | None:
        """Per-attempt state fixed at the start, e.g. the order of options."""
        return None

    @abstractmethod
    def content(self, payload: P, state: Stored | None) -> ApiModel:
        """What the candidate sees: never the correct answer or anything it can be derived from."""

    @abstractmethod
    def store_answer(self, payload: P, state: Stored | None, answer: Stored) -> Stored:
        """Validates what the candidate sent and turns it into the stored form."""

    @abstractmethod
    def show_answer(self, payload: P, state: Stored | None, stored: Stored) -> ApiModel:
        """The stored answer as the candidate entered it."""

    @abstractmethod
    async def grade(self, payload: P, stored: Stored, runner: CodeRunner) -> float | None:
        """Share of the task earned, 0–1. None = a person has to grade it."""

    @abstractmethod
    def review(self, payload: P, state: Stored | None, stored: Stored | None) -> Stored:
        """The answer next to what was expected, for the author of the test."""
