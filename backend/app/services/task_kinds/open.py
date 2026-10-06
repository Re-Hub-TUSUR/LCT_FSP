from typing import ClassVar

from pydantic import ValidationError

from app.core.errors import AppError
from app.models import TaskKind
from app.schemas.assessment import OpenAnswer, OpenContent, OpenPayload
from app.services.code_runner import CodeRunner
from app.services.task_kinds.base import Stored, TaskKindSpec


class OpenKind(TaskKindSpec[OpenPayload]):
    """Free-text answer the author of the test grades by hand."""

    kind: ClassVar = TaskKind.OPEN
    manual: ClassVar = True

    def content(self, payload: OpenPayload, state: Stored | None) -> OpenContent:
        return OpenContent(max_length=payload.max_length)

    def store_answer(self, payload: OpenPayload, state: Stored | None, answer: Stored) -> Stored:
        try:
            text = OpenAnswer.model_validate(answer).text
        except ValidationError as exc:
            raise AppError("Передайте текст ответа") from exc
        if len(text) > payload.max_length:
            raise AppError(f"Ответ длиннее {payload.max_length} символов")
        return {"text": text}

    def show_answer(self, payload: OpenPayload, state: Stored | None, stored: Stored) -> OpenAnswer:
        return OpenAnswer.model_validate(stored)

    async def grade(self, payload: OpenPayload, stored: Stored, runner: CodeRunner) -> float | None:
        # An empty answer earns nothing and needs nobody's time.
        return None if stored.get("text", "").strip() else 0.0

    def review(self, payload: OpenPayload, state: Stored | None, stored: Stored | None) -> Stored:
        return {"text": stored.get("text", "") if stored else "", "guidance": payload.guidance}
