import uuid
from datetime import datetime
from typing import Annotated, Any, Literal, Self

from pydantic import AwareDatetime, Field, ValidationError, model_validator

from app.models.enums import (
    AssessmentStatus,
    AssignmentStatus,
    AttemptStatus,
    Grade,
    TaskDifficulty,
    TaskKind,
)
from app.schemas.common import ApiModel

# onlinecompiler.io cuts stdout at 999 characters: a longer expected output could never match.
MAX_EXPECTED_OUTPUT = 900
MAX_CODE_LENGTH = 50_000
MAX_INPUT_LENGTH = 60_000
MAX_IMPORT_TASKS = 500

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


class OpenPayload(ApiModel):
    """Free-text answer graded by the author of the test."""

    max_length: int = Field(default=4000, ge=100, le=20_000)
    # What a good answer covers. Reviewers only: the candidate never sees it.
    guidance: str | None = Field(default=None, max_length=4000)


# Content of a task by kind. A new kind registers its model here and its behaviour in
# `app.services.task_kinds`.
PAYLOAD_MODELS: dict[TaskKind, type[ApiModel]] = {
    TaskKind.QUIZ: QuizPayload,
    TaskKind.CODE: CodePayload,
    TaskKind.OPEN: OpenPayload,
}


class TaskWrite(ApiModel):
    """A task as authors write it. Also the format of bank export and import files."""

    kind: TaskKind
    difficulty: TaskDifficulty
    specializations: list[str] = Field(default_factory=list)
    topic: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    statement: str = Field(min_length=1, max_length=20_000)
    # Kind-specific content, see `PAYLOAD_MODELS`.
    payload: dict[str, Any]
    is_active: bool = True

    @model_validator(mode="after")
    def _payload_matches_kind(self) -> Self:
        try:
            content = PAYLOAD_MODELS[self.kind].model_validate(self.payload)
        except ValidationError as exc:
            problems = "; ".join(
                f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
                for error in exc.errors()
            )
            msg = f"payload of a {self.kind} task: {problems}"
            raise ValueError(msg) from exc
        # Normalised and in the wire spelling, so a read task can be written back as it is.
        self.payload = content.model_dump(mode="json", by_alias=True)
        return self


class TaskRead(TaskWrite):
    id: uuid.UUID
    # True for the platform bank, false for an employer's own task.
    platform: bool
    created_at: datetime


class ImportResult(ApiModel):
    created: int


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
    # Platform templates: null = the test of the grade for every specialization.
    specialization: str | None = None
    duration_minutes: int = Field(ge=5, le=180)
    pass_score: int = Field(default=60, ge=0, le=100)
    quiz_weight: int = Field(default=40, ge=0, le=100)
    composition: Composition
    # Days before a retake after a failure / before a confirmed grade can be changed.
    # Null = the platform defaults.
    retry_days: int | None = Field(default=None, ge=0, le=365)
    grade_change_days: int | None = Field(default=None, ge=0, le=365)
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


class QuizContent(ApiModel):
    # In the order shown to this candidate.
    options: list[str]
    multiple: bool


class QuizAnswer(ApiModel):
    # Positions in the option list as it was shown to the candidate.
    selected: list[int] = Field(max_length=8)


class CodeContent(ApiModel):
    languages: list[LanguageOption]
    time_limit: float
    samples: list[SampleTest]


class CodeAnswer(ApiModel):
    language: str
    code: str = Field(max_length=MAX_CODE_LENGTH)


class OpenContent(ApiModel):
    max_length: int


class OpenAnswer(ApiModel):
    text: str


class AttemptTask(ApiModel):
    id: uuid.UUID
    kind: TaskKind
    topic: str
    difficulty: TaskDifficulty
    title: str
    statement: str
    # Both depend on the kind: `QuizContent` + `QuizAnswer`, `CodeContent` + `CodeAnswer`, …
    content: dict[str, Any]
    # Null until the candidate answers.
    answer: dict[str, Any] | None


class TopicResult(ApiModel):
    topic: str
    kind: TaskKind
    # Share of the topic's tasks earned, 0–1.
    earned: float
    total: int


class AttemptRead(ApiModel):
    id: uuid.UUID
    # Set for a test a company sent; null for a platform grade test.
    assignment_id: uuid.UUID | None
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
    # The answer model of the task's kind.
    answer: dict[str, Any]


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


class TrackRead(ApiModel):
    """One specialization the candidate has tried: its own category and its own cooldown."""

    specialization: str
    # `passed`: the grade below is confirmed; `failed`: tried and nothing is confirmed yet.
    status: AssessmentStatus
    grade: Grade | None
    score: float | None
    # Null = a test of this specialization may start right now.
    next_attempt_at: datetime | None
    # The category employers see in search and feeds.
    is_primary: bool


class AssessmentStatusRead(ApiModel):
    """Candidate's categorisation state and what they may do next."""

    # The primary category, i.e. what employers see; the fields are null until one is confirmed.
    status: AssessmentStatus
    specialization: str | None
    grade: Grade | None
    score: float | None
    next_attempt_at: datetime | None
    # Every specialization the candidate has tried, confirmed ones first.
    tracks: list[TrackRead]
    active_attempt_id: uuid.UUID | None
    # False while the code runner has no API key: code tasks cannot be checked.
    code_runner_available: bool
    history: list[AttemptRead]


class PrimaryCategory(ApiModel):
    specialization: str


class TemplateRead(ApiModel):
    """What a platform grade test consists of, shown before the candidate starts it."""

    grade: Grade
    # Null = applies to every specialization without its own template.
    specialization: str | None
    duration_minutes: int
    pass_score: int
    # Task kind → number of tasks in a variant.
    tasks: dict[TaskKind, int]
    retry_days: int
    grade_change_days: int


class SurveyAnswers(ApiModel):
    """Onboarding survey: industry and specialization (first step of the mandatory path)."""

    industry: str
    specialization: str
    answers: dict[str, Any]


# ── Employer's test assignments («тестовые») ──────────────────────────────────────────────────


class NamedRef(ApiModel):
    id: uuid.UUID
    name: str


class AssignmentCreate(ApiModel):
    test_id: uuid.UUID
    candidate_id: uuid.UUID
    vacancy_id: uuid.UUID | None = None
    message: str | None = Field(default=None, max_length=2000)
    # Until when the candidate may start; a week from now by default.
    due_at: AwareDatetime | None = None


class AssignmentRead(ApiModel):
    """A test a company sent to a candidate, as both sides see it in their lists."""

    id: uuid.UUID
    title: str
    status: AssignmentStatus
    company: NamedRef
    candidate: NamedRef
    vacancy: NamedRef | None
    message: str | None
    duration_minutes: int
    tasks_count: int
    created_at: datetime
    due_at: datetime
    # Set once the candidate started.
    attempt_id: uuid.UUID | None
    finished_at: datetime | None
    # Null until every answer is graded.
    score: float | None
    pass_score: int | None


class ReviewTask(ApiModel):
    id: uuid.UUID
    kind: TaskKind
    title: str
    statement: str
    answered: bool
    # Share of the task earned, 0–1; null = waits for the reviewer.
    points: float | None
    # True: `points` is set by the reviewer, not by the platform.
    manual: bool
    comment: str | None
    # The answer next to what was expected; the shape depends on the kind.
    review: dict[str, Any]


class AssignmentDetail(AssignmentRead):
    """Employer's view of a taken test: answers, points and anti-cheat signals."""

    tasks: list[ReviewTask]
    paste_count: int
    blur_count: int


class ReviewGrade(ApiModel):
    task_id: uuid.UUID
    points: float = Field(ge=0, le=1)
    comment: str | None = Field(default=None, max_length=2000)


class ReviewRequest(ApiModel):
    grades: list[ReviewGrade] = Field(min_length=1, max_length=60)
