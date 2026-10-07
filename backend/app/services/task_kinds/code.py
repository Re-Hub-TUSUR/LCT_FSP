import asyncio
from typing import ClassVar

from pydantic import ValidationError

from app.core.errors import AppError
from app.models import TaskKind
from app.schemas.assessment import (
    CodeAnswer,
    CodeContent,
    CodeContext,
    CodePayload,
    LanguageOption,
    SampleTest,
    Verdict,
)
from app.services.code_runner import COMPILERS, CodeRunner, Execution
from app.services.task_kinds.base import Stored, TaskKindSpec


def allowed_languages(payload: CodePayload) -> list[str]:
    """Compiler ids a candidate may pick, in the order of the language menu."""
    return [
        language for language in COMPILERS if not payload.languages or language in payload.languages
    ]


def normalize_output(text: str) -> str:
    """Trailing spaces and blank lines around the output never decide a verdict."""
    lines = text.replace("\r\n", "\n").strip().split("\n")
    return "\n".join(line.rstrip() for line in lines)


def judge(execution: Execution, expected: str, time_limit: float) -> Verdict:
    if execution.killed or (execution.time is not None and execution.time > time_limit):
        return "time_limit"
    if not execution.ok:
        return "runtime_error"
    if normalize_output(execution.output) == normalize_output(expected):
        return "ok"
    return "wrong_answer"


class CodeKind(TaskKindSpec[CodePayload]):
    """stdin/stdout program. Open groups serve "Run"; hidden ones decide the score on finish."""

    kind: ClassVar = TaskKind.CODE
    code_group: ClassVar = True

    def check(self, payload: CodePayload) -> None:
        languages = [
            *payload.languages,
            *([payload.reference.language] if payload.reference else []),
        ]
        unsupported = [language for language in languages if language not in COMPILERS]
        if unsupported:
            raise AppError("Неподдерживаемый язык", details={"languages": unsupported})
        if payload.reference and payload.reference.language not in allowed_languages(payload):
            raise AppError("Язык эталонного решения не разрешён в задаче")

    def content(self, payload: CodePayload, state: Stored | None) -> CodeContent:
        return CodeContent(
            languages=[
                LanguageOption(id=language, label=COMPILERS[language])
                for language in allowed_languages(payload)
            ],
            time_limit=payload.time_limit,
            samples=[
                SampleTest(input=group.input, expected=group.expected)
                for group in payload.groups
                if not group.hidden
            ],
        )

    def store_answer(self, payload: CodePayload, state: Stored | None, answer: Stored) -> Stored:
        try:
            draft = CodeAnswer.model_validate(answer)
        except ValidationError as exc:
            raise AppError("Передайте язык и код решения") from exc
        self.check_language(payload, draft.language)
        return {"language": draft.language, "code": draft.code}

    def show_answer(self, payload: CodePayload, state: Stored | None, stored: Stored) -> CodeAnswer:
        return CodeAnswer.model_validate(stored)

    async def grade(self, payload: CodePayload, stored: Stored, runner: CodeRunner) -> float:
        hidden = [group for group in payload.groups if group.hidden]
        executions = await asyncio.gather(
            *(
                runner.run(compiler=stored["language"], code=stored["code"], stdin=group.input)
                for group in hidden
            )
        )
        passed = sum(
            judge(execution, group.expected, payload.time_limit) == "ok"
            for group, execution in zip(hidden, executions, strict=True)
        )
        return passed / len(hidden)

    def review(self, payload: CodePayload, state: Stored | None, stored: Stored | None) -> Stored:
        return {
            "language": COMPILERS.get(stored["language"], stored["language"]) if stored else None,
            "code": stored["code"] if stored else None,
        }

    def context(
        self, payload: CodePayload, state: Stored | None, stored: Stored | None, points: float
    ) -> CodeContext:
        hidden = sum(group.hidden for group in payload.groups)
        sample = next((group for group in payload.groups if not group.hidden), None)
        reference = payload.reference
        return CodeContext(
            language=COMPILERS.get(stored["language"], stored["language"]) if stored else None,
            code=stored["code"] if stored else None,
            tests_passed=round(points * hidden),
            tests_total=hidden,
            time_limit=payload.time_limit,
            sample=SampleTest(input=sample.input, expected=sample.expected) if sample else None,
            reference_language=(
                COMPILERS.get(reference.language, reference.language) if reference else None
            ),
            reference_code=reference.code if reference else None,
        )

    @staticmethod
    def check_language(payload: CodePayload, language: str) -> None:
        if language not in allowed_languages(payload):
            raise AppError("Этот язык недоступен для задачи")
