"""A finished grade test as context for an LLM interviewer.

The model that asks the candidate follow-up questions and gives the final mark is not here:
this module only prepares what it reads. `AttemptContextService.build` returns the structure,
`render_context` turns it into a text block for a prompt.

The context holds the correct answers and reference solutions. Hand it to the model, never to
the candidate.
"""

import uuid
from typing import Final

from app.core.errors import ConflictError, NotFoundError
from app.models import AttemptStatus, TaskDifficulty, TaskKind
from app.repositories.assessment import AssessmentRepository
from app.schemas.assessment import (
    AttemptContext,
    CodeContext,
    Outcome,
    QuizContext,
    TaskContext,
    TopicResult,
)
from app.services.assessments import attempt_tasks
from app.services.categories import GRADE_LABELS, SPECIALIZATIONS
from app.services.task_kinds import spec_of

MAX_STATEMENT: Final = 1500
MAX_CODE: Final = 4000
MAX_REFERENCE: Final = 2500
CUT: Final = " … (обрезано)"

KIND_LABELS: Final = {
    TaskKind.QUIZ: "Вопрос",
    TaskKind.CODE: "Задача на код",
    TaskKind.OPEN: "Открытый вопрос",
}
DIFFICULTY_LABELS: Final = {
    TaskDifficulty.EASY: "лёгкая",
    TaskDifficulty.MEDIUM: "средняя",
    TaskDifficulty.HARD: "сложная",
}
OUTCOME_LABELS: Final[dict[Outcome, str]] = {
    "correct": "верно",
    "partial": "частично",
    "wrong": "неверно",
    "unanswered": "нет ответа",
}


class AttemptContextService:
    def __init__(self, assessments: AssessmentRepository) -> None:
        self._assessments = assessments

    async def build(self, attempt_id: uuid.UUID) -> AttemptContext:
        attempt = await self._assessments.get_attempt(attempt_id)
        if attempt is None:
            raise NotFoundError("Попытка не найдена")
        graded = attempt.status in (AttemptStatus.PASSED, AttemptStatus.FAILED)
        if (
            attempt.assignment_id is not None
            or attempt.specialization is None
            or attempt.grade is None
            or attempt.score is None
            or attempt.finished_at is None
            or not graded
        ):
            raise ConflictError("Контекст собирается только для завершённого теста на грейд")

        answers = await self._assessments.answers_of(attempt.id)
        tasks = []
        for number, task in enumerate(attempt_tasks(attempt), start=1):
            answer = answers.get(task.id)
            points = (answer.points or 0.0) if answer else 0.0
            spec = spec_of(task)
            tasks.append(
                TaskContext(
                    number=number,
                    kind=task.kind,
                    topic=task.topic,
                    difficulty=task.difficulty,
                    title=task.title,
                    statement=task.statement,
                    outcome=_outcome(answered=answer is not None, points=points),
                    points=points,
                    detail=spec.context(
                        spec.payload(task),
                        attempt.task_state.get(str(task.id)),
                        answer.answer if answer else None,
                        points,
                    ),
                )
            )
        spent = attempt.finished_at - attempt.started_at
        return AttemptContext(
            attempt_id=attempt.id,
            title=attempt.title,
            specialization=attempt.specialization,
            grade=attempt.grade,
            score=attempt.score,
            pass_score=attempt.pass_score,
            passed=attempt.status == AttemptStatus.PASSED,
            minutes_spent=max(0, round(spent.total_seconds() / 60)),
            breakdown=[TopicResult.model_validate(item) for item in attempt.breakdown or []],
            paste_count=attempt.paste_count,
            blur_count=attempt.blur_count,
            runs_count=attempt.runs_count,
            tasks=tasks,
        )


def render_context(context: AttemptContext, *, max_chars: int = 12_000) -> str:
    """The context as a text block for a prompt, at most `max_chars` long.

    Tasks the candidate got wrong and code tasks come in full: these are what an interviewer
    asks about. A correctly answered question takes one line, and when the text does not fit,
    such questions are dropped from the end first.
    """
    head = _head(context)
    blocks = [(_task(task), _droppable(task)) for task in context.tasks]

    def text(dropped: int) -> str:
        parts = [head, *(block for block, _ in blocks)]
        if dropped:
            parts.append(f"Ещё верных ответов опущено: {dropped}.")
        return "\n\n".join(parts)

    dropped = 0
    while len(text(dropped)) > max_chars:
        last = next((i for i in reversed(range(len(blocks))) if blocks[i][1]), None)
        if last is None:
            break
        del blocks[last]
        dropped += 1
    result = text(dropped)
    return result if len(result) <= max_chars else _clip(result, max_chars)


def _outcome(*, answered: bool, points: float) -> Outcome:
    if not answered:
        return "unanswered"
    if points >= 1:
        return "correct"
    return "partial" if points > 0 else "wrong"


def _droppable(task: TaskContext) -> bool:
    return isinstance(task.detail, QuizContext) and task.outcome == "correct"


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: max(0, limit - len(CUT))].rstrip() + CUT


def _number(value: float) -> str:
    return f"{value:g}".replace(".", ",")


def _indent(code: str) -> str:
    return "\n".join(f"    {line}" for line in code.rstrip().split("\n"))


def _head(context: AttemptContext) -> str:
    specialization = SPECIALIZATIONS.get(context.specialization, context.specialization)
    verdict = "сдан" if context.passed else "не сдан"
    lines = [
        f"## Тест: {specialization} · {GRADE_LABELS[context.grade]} — "
        f"{_number(context.score)} из 100 ({verdict}, проходной балл {context.pass_score})",
        f"Время: {context.minutes_spent} мин. Вставок из буфера: {context.paste_count}, "
        f"уходов со вкладки: {context.blur_count}, запусков кода: {context.runs_count}.",
    ]
    if context.breakdown:
        lines.append("")
        lines.append("По темам:")
        lines += [
            f"- {item.topic} ({KIND_LABELS[item.kind].lower()}): "
            f"{round(item.earned * 100)}%, заданий: {item.total}"
            for item in context.breakdown
        ]
    return "\n".join(lines)


def _task(task: TaskContext) -> str:
    detail = task.detail
    result = OUTCOME_LABELS[task.outcome]
    if isinstance(detail, CodeContext):
        result = f"{detail.tests_passed} из {detail.tests_total} закрытых тестов"
    lines = [
        f"### {task.number}. {KIND_LABELS[task.kind]} · {task.topic} · "
        f"{DIFFICULTY_LABELS[task.difficulty]} · {result}"
    ]
    if isinstance(detail, QuizContext):
        lines.append(_clip(task.statement, MAX_STATEMENT))
        if task.outcome == "correct":
            chosen = "; ".join(option.text for option in detail.options if option.chosen)
            lines.append(f"Ответ кандидата: {chosen}")
        else:
            lines += [
                _option(option.text, option.chosen, option.correct) for option in detail.options
            ]
            if task.outcome == "unanswered":
                lines.append("Кандидат не ответил.")
    elif isinstance(detail, CodeContext):
        lines.append(task.title)
        lines.append(_clip(task.statement, MAX_STATEMENT))
        if detail.code is None:
            lines.append("Решение не отправлено.")
        else:
            lines.append(f"Решение кандидата ({detail.language}):")
            lines.append(_indent(_clip(detail.code, MAX_CODE)))
        if detail.reference_code is not None:
            lines.append(f"Эталонное решение ({detail.reference_language}):")
            lines.append(_indent(_clip(detail.reference_code, MAX_REFERENCE)))
    else:
        lines.append(_clip(task.statement, MAX_STATEMENT))
        lines.append(f"Ответ кандидата: {_clip(detail.text, MAX_CODE) or '—'}")
        if detail.guidance:
            lines.append(f"Что ожидалось: {_clip(detail.guidance, MAX_REFERENCE)}")
    return "\n".join(lines)


def _option(text: str, chosen: bool, correct: bool) -> str:
    marks = [mark for mark, on in (("выбран", chosen), ("верный", correct)) if on]
    return f"- [{', '.join(marks)}] {text}" if marks else f"- {text}"
