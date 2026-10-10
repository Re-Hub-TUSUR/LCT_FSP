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
    # Share of a hidden group in the score of the task, relative to the other hidden groups.
    weight: int = Field(default=1, ge=1, le=10)


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
    # Compiler id → the code the editor opens with instead of the empty template: a program to
    # fix or to refactor. The hidden groups still decide the score.
    starter: dict[str, Annotated[str, Field(min_length=1, max_length=MAX_CODE_LENGTH)]] = Field(
        default_factory=dict
    )

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
    # What the editor should fix although the task is saved (e.g. a right option that gives
    # itself away by its length).
    warnings: list[str] = Field(default_factory=list)


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
    # A pass needs this share of the quiz right, percent, whatever the code earned.
    quiz_min: int = Field(default=0, ge=0, le=100)
    # Platform templates: the grade is offered, but its confirmation is shown as provisional.
    is_beta: bool = False
    composition: Composition
    # Days before a retake after a failure / before a confirmed grade can be changed.
    # Null = the platform defaults.
    retry_days: int | None = Field(default=None, ge=0, le=365)
    grade_change_days: int | None = Field(default=None, ge=0, le=365)
    # A pass with at least this score opens the next grade at once. Null = the platform default.
    recommend_score: int | None = Field(default=None, ge=0, le=100)
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
    # Compiler id → the code to start from; a language without one starts from the template.
    starter: dict[str, str] = Field(default_factory=dict)


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
    # The least share of the quiz right a pass needs, percent.
    quiz_min: int = 0
    is_beta: bool = False
    started_at: datetime
    expires_at: datetime
    finished_at: datetime | None
    # Filled once the attempt is finished.
    breakdown: list[TopicResult] | None = None
    # Share of the quiz answered right, percent: null while unfinished or without a quiz.
    quiz_share: float | None = None
    # In the answer to "finish" only: the grade this result opens, if it was good enough.
    recommended_grade: Grade | None = None
    # Why a failed attempt failed: too few points, the quiz below its minimum, or the AI
    # interview after a pass on points. Null for any other status.
    failed_by: Literal["score", "quiz", "interview"] | None = None


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


class AttemptTime(ApiModel):
    """Time spent on one task since the last report, in seconds."""

    task_id: uuid.UUID
    seconds: float = Field(gt=0, le=24 * 3600)


class AttemptSignal(ApiModel):
    kind: Literal["paste", "blur"]


class Recommendation(ApiModel):
    """The next grade a well-passed test opened: no wait for the grade-change cooldown."""

    grade: Grade
    # Null = may start right now; a date after a failed try at it.
    next_attempt_at: datetime | None


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
    recommendation: Recommendation | None = None
    # Grade of the failed test that started the pause: tests of lower grades are open at once.
    failed_grade: Grade | None = None
    is_beta: bool = False


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
    # A grade test passed on points whose AI interview is not answered yet.
    interview_attempt_id: uuid.UUID | None = None
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
    quiz_min: int
    is_beta: bool
    # Task kind → number of tasks in a variant.
    tasks: dict[TaskKind, int]
    retry_days: int
    grade_change_days: int
    recommend_score: int


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


# ── Attempt context for the follow-up interview ───────────────────────────────────────────────
# Internal: it carries the correct answers, so no endpoint may return it to the candidate.

Outcome = Literal["correct", "partial", "wrong", "unanswered"]


class QuizOptionContext(ApiModel):
    text: str
    chosen: bool
    correct: bool


class QuizContext(ApiModel):
    # In the order the candidate saw them.
    options: list[QuizOptionContext]
    multiple: bool


class CodeContext(ApiModel):
    # Name of the language and the last saved solution; null when nothing was submitted.
    language: str | None
    code: str | None
    # Hidden test groups. Only the share earned survives the grading, not which of them failed:
    # with unequal weights the number of passed groups is an estimate.
    tests_passed: int
    tests_total: int
    time_limit: float
    # The first open test group, the one shown to the candidate.
    sample: SampleTest | None
    reference_language: str | None
    reference_code: str | None


class OpenContext(ApiModel):
    text: str
    # What a good answer covers, written by the author of the task.
    guidance: str | None


class TaskContext(ApiModel):
    # Position in the test, from 1.
    number: int
    kind: TaskKind
    topic: str
    difficulty: TaskDifficulty
    title: str
    statement: str
    outcome: Outcome
    # Share of the task earned, 0–1.
    points: float
    detail: QuizContext | CodeContext | OpenContext


class AttemptContext(ApiModel):
    """A finished grade test as an interviewer needs it: every task, what the candidate
    answered and what was expected. No personal data of the candidate."""

    attempt_id: uuid.UUID
    title: str
    specialization: str
    grade: Grade
    score: float
    pass_score: int
    passed: bool
    minutes_spent: int
    breakdown: list[TopicResult]
    # Signals for the interviewer; they never changed the score.
    paste_count: int
    blur_count: int
    runs_count: int
    tasks: list[TaskContext]


# ── AI interview about the candidate's code (`app.services.interview`) ────────────────────────

InterviewStatus = Literal["asked", "passed", "failed"]
MAX_INTERVIEW_ANSWER = 2000


class InterviewQuestion(ApiModel):
    # Position in the interview, from 1.
    number: int
    # The code task the question is about.
    task_title: str
    text: str


class InterviewMark(ApiModel):
    number: int
    score: int
    comment: str


class InterviewResult(ApiModel):
    # Mark of the answers, 0–100; the grade is confirmed from `pass_score` up. Null when the
    # interview was skipped or the time ran out.
    score: float | None
    pass_score: int
    passed: bool
    summary: str
    marks: list[InterviewMark]


class InterviewRead(ApiModel):
    attempt_id: uuid.UUID
    status: InterviewStatus
    questions: list[InterviewQuestion]
    # Answers are accepted until then.
    deadline: datetime | None
    result: InterviewResult | None


class InterviewAnswers(ApiModel):
    # One per question, in the order of the questions.
    answers: list[Annotated[str, Field(max_length=MAX_INTERVIEW_ANSWER)]] = Field(
        min_length=1, max_length=5
    )


class InterviewQuestionState(ApiModel):
    # Number of the code task in the test.
    task: int
    task_title: str
    text: str


class InterviewState(ApiModel):
    """What `AssessmentAttempt.interview` stores. Holds the candidate's answers: candidate's
    own view and the model only."""

    questions: list[InterviewQuestionState] = Field(default_factory=list)
    asked_at: AwareDatetime | None = None
    answers: list[str] | None = None
    answered_at: AwareDatetime | None = None
    marks: list[InterviewMark] = Field(default_factory=list)
    score: float | None = None
    summary: str = ""
    passed: bool | None = None
    model: str = ""
