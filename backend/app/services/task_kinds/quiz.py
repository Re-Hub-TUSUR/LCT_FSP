import secrets
from typing import ClassVar

from pydantic import ValidationError

from app.core.errors import AppError
from app.models import TaskKind
from app.schemas.assessment import QuizAnswer, QuizContent, QuizPayload
from app.services.code_runner import CodeRunner
from app.services.task_kinds.base import Stored, TaskKindSpec

_random = secrets.SystemRandom()


class QuizKind(TaskKindSpec[QuizPayload]):
    """Choice question. Options are shuffled per attempt; answers are stored as bank indexes."""

    kind: ClassVar = TaskKind.QUIZ

    def new_state(self, payload: QuizPayload) -> Stored:
        # position shown to the candidate → index in the bank
        return {"order": _random.sample(range(len(payload.options)), len(payload.options))}

    def content(self, payload: QuizPayload, state: Stored | None) -> QuizContent:
        return QuizContent(
            options=[payload.options[index] for index in _order(payload, state)],
            multiple=payload.multiple,
        )

    def store_answer(self, payload: QuizPayload, state: Stored | None, answer: Stored) -> Stored:
        try:
            selected = list(dict.fromkeys(QuizAnswer.model_validate(answer).selected))
        except ValidationError as exc:
            raise AppError("Некорректный вариант ответа") from exc
        order = _order(payload, state)
        if any(not 0 <= position < len(order) for position in selected) or (
            len(selected) > 1 and not payload.multiple
        ):
            raise AppError("Некорректный вариант ответа")
        return {"selected": sorted(order[position] for position in selected)}

    def show_answer(self, payload: QuizPayload, state: Stored | None, stored: Stored) -> QuizAnswer:
        chosen = set(stored.get("selected", []))
        return QuizAnswer(
            selected=[
                position for position, index in enumerate(_order(payload, state)) if index in chosen
            ]
        )

    async def grade(self, payload: QuizPayload, stored: Stored, runner: CodeRunner) -> float:
        return float(sorted(stored.get("selected", [])) == sorted(payload.correct))

    def review(self, payload: QuizPayload, state: Stored | None, stored: Stored | None) -> Stored:
        return {
            "options": payload.options,
            "correct": sorted(payload.correct),
            "selected": sorted(stored.get("selected", [])) if stored else [],
        }


def _order(payload: QuizPayload, state: Stored | None) -> list[int]:
    order = (state or {}).get("order")
    return list(order) if order else list(range(len(payload.options)))
