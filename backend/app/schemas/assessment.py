import uuid
from datetime import datetime
from typing import Annotated, Any, Literal, Self

from pydantic import Field, model_validator

from app.models.enums import AssessmentStatus, AttemptStatus, Grade, TaskDifficulty, TaskKind
from app.schemas.common import ApiModel

# onlinecompiler.io cuts stdout at 999 characters: a longer expected output could never match.
MAX_EXPECTED_OUTPUT = 900
MAX_CODE_LENGTH = 50_000
MAX_INPUT_LENGTH = 60_000

Verdict = Literal["ok", "wrong_answer", "runtime_error", "time_limit"]


# ── Task bank (author view: admins and task owners only) ──────────────────────────────────────


class QuizPayload(ApiModel):
    options: list[Annotated[str, Field(min_length=1, max_length=500)]] = Field(
        min_length=2, max_length=8
    )
    # Indexes into `options`.
    correct: list[int] = Field(min_length=1)
    multiple: bool = False

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if len(set(self.correct)) != len(self.correct) or not all(
            0 <= index < len(self.options) for index in self.correct
        ):
            msg = "correct must hold unique indexes of options"
            raise ValueError(msg)
        if not self.multiple and len(self.correct) != 1:
            msg = "a single-choice question has exactly one correct option"
            raise ValueError(msg)
        return self


class TestGroup(ApiModel):
    """One run of the program: stdin and the exact stdout it must print."""

    input: str = Field(max_length=MAX_INPUT_LENGTH)
    expected: str = Field(min_length=1, max_length=MAX_EXPECTED_OUTPUT)
    # Open groups are shown to the candidate and used by "Run"; hidden ones decide the score.
    hidden: bool = False


class ReferenceSolution(ApiModel):
    language: str
    code: str = Field(min_length=1, max_length=MAX_CODE_LENGTH)


class CodePayload(ApiModel):
    # Compiler ids the candidate may use; empty = every supported language.
    languages: list[str] = Field(default_factory=list)
    time_limit: float = Field(default=5, gt=0, le=20)
    groups: list[TestGroup] = Field(min_length=2, max_length=8)
    # Author's solution: "check" runs it against every group before the task goes live.
    reference: ReferenceSolution | None = None

    @model_validator(mode="after")
    def _open_and_hidden(self) -> Self:
        hidden = sum(group.hidden for group in self.groups)
        if hidden == 0 or hidden == len(self.groups):
            msg = "a code task needs at least one open and one hidden test group"
            raise ValueError(msg)
        return self


class TaskWrite(ApiModel):
    kind: TaskKind
    difficulty: TaskDifficulty
    specializations: list[str] = Field(default_factory=list)
    topic: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    statement: str = Field(min_length=1, max_length=20_000)
    quiz: QuizPayload | None = None
    code: CodePayload | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def _payload_matches_kind(self) -> Self:
        if (self.kind == TaskKind.QUIZ) != (self.quiz is not None) or (
            self.kind == TaskKind.CODE
        ) != (self.code is not None):
            msg = "pass `quiz` for a quiz task and `code` for a code task"
            raise ValueError(msg)
        return self


class TaskRead(TaskWrite):
    id: uuid.UUID
    # True for the platform bank, false for an employer's own task.
    platform: bool
    created_at: datetime


class CompositionRule(ApiModel):
    kind: TaskKind
    count: int = Field(ge=1, le=40)
    # Empty = any.
    difficulty: list[TaskDifficulty] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    # specialization: tasks tagged with the candidate's specialization; general: untagged ones.
    scope: Literal["specialization", "general", "any"] = "any"


class RulesComposition(ApiModel):
    """A variant is drawn from the bank for every attempt."""

    mode: Literal["rules"] = "rules"
    rules: list[CompositionRule] = Field(min_length=1, max_length=12)


class FixedComposition(ApiModel):
    """Every candidate gets exactly these tasks."""

    mode: Literal["fixed"] = "fixed"
    task_ids: list[uuid.UUID] = Field(min_length=1, max_length=60)


Composition = Annotated[RulesComposition | FixedComposition, Field(discriminator="mode")]


class TestWrite(ApiModel):
    title: str = Field(min_length=1, max_length=200)
    # Platform templates: the grade the test confirms. Always null for an employer's test.
    grade: Grade | None = None
    duration_minutes: int = Field(ge=5, le=180)
    pass_score: int = Field(default=60, ge=0, le=100)
    quiz_weight: int = Field(default=40, ge=0, le=100)
    composition: Composition
    is_active: bool = True


class TestRead(TestWrite):
    id: uuid.UUID
    platform: bool
    created_at: datetime


class GroupCheck(ApiModel):
    hidden: bool
    verdict: Verdict
    output: str
    error: str
    time: float | None


class TaskCheck(ApiModel):
    """Result of running the reference solution against every group of a code task."""

    ok: bool
    groups: list[GroupCheck]


# ── Candidate view: never carries correct options or hidden groups ────────────────────────────


class LanguageOption(ApiModel):
    id: str
    label: str


class SampleTest(ApiModel):
    input: str
    expected: str


class QuizAnswer(ApiModel):
    # Positions in the option list as it was shown to the candidate.
    selected: list[int]


class CodeAnswer(ApiModel):
    language: str
    code: str


class AttemptTask(ApiModel):
    id: uuid.UUID
    kind: TaskKind
    topic: str
    difficulty: TaskDifficulty
    title: str
    statement: str
    # Quiz only.
    options: list[str] | None = None
    multiple: bool | None = None
    selected: list[int] | None = None
    # Code only.
    languages: list[LanguageOption] | None = None
    time_limit: float | None = None
    samples: list[SampleTest] | None = None
    draft: CodeAnswer | None = None


class TopicResult(ApiModel):
    topic: str
    kind: TaskKind
    # Share of the topic's tasks earned, 0–1.
    earned: float
    total: int


class AttemptRead(ApiModel):
    id: uuid.UUID
    title: str
    specialization: str | None
    grade: Grade | None
    status: AttemptStatus
    score: float | None
    pass_score: int
    started_at: datetime
    expires_at: datetime
    finished_at: datetime | None
    # Filled once the attempt is finished.
    breakdown: list[TopicResult] | None = None


class AttemptDetail(AttemptRead):
    tasks: list[AttemptTask]
    runs_left: int
    # Server clock, so the countdown does not depend on the candidate's device time.
    server_time: datetime


class AttemptStart(ApiModel):
    specialization: str
    grade: Grade


class AttemptAnswer(ApiModel):
    task_id: uuid.UUID
    selected: list[int] | None = Field(default=None, max_length=8)
    language: str | None = None
    code: str | None = Field(default=None, max_length=MAX_CODE_LENGTH)


class RunRequest(ApiModel):
    task_id: uuid.UUID
    language: str
    code: str = Field(min_length=1, max_length=MAX_CODE_LENGTH)
    # Own stdin instead of the open tests.
    input: str | None = Field(default=None, max_length=MAX_INPUT_LENGTH)


class RunResult(ApiModel):
    # Null for a run on the candidate's own input: there is nothing to compare with.
    verdict: Verdict | None
    input: str
    expected: str | None
    output: str
    error: str
    time: float | None


class RunResponse(ApiModel):
    results: list[RunResult]
    runs_left: int


class AttemptSignal(ApiModel):
    kind: Literal["paste", "blur"]


class AssessmentStatusRead(ApiModel):
    """Candidate's categorisation state and what they may do next."""

    status: AssessmentStatus
    specialization: str | None
    grade: Grade | None
    score: float | None
    active_attempt_id: uuid.UUID | None
    # Null = a new attempt may start right now.
    next_attempt_at: datetime | None
    # False while the code runner has no API key: code tasks cannot be checked.
    code_runner_available: bool
    history: list[AttemptRead]


class SurveyAnswers(ApiModel):
    """Onboarding survey: industry and specialization (first step of the mandatory path)."""

    industry: str
    specialization: str
    answers: dict[str, Any]
