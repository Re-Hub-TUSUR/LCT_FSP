"""Contracts of the admin API (camelCase on the wire, like the rest of the API)."""

import re
import uuid
from datetime import datetime
from typing import Annotated, Any, Literal, Self

from pydantic import Field, field_validator, model_validator

from app.admin.enums import AnalyticsPeriod, EmployerCaseStatus, TaskStatus, VerificationStatus
from app.models.enums import TaskDifficulty, TaskKind
from app.schemas.common import ApiModel

_VARIABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,31}$")
_INN = re.compile(r"^(\d{10}|\d{12})$")
_DOMAIN = re.compile(r"^(?=.{3,255}$)([a-z0-9-]+\.)+[a-z]{2,}$")

# ── Common ──────────────────────────────────────────────────────────────────────────────────────


class AuditEntryRead(ApiModel):
    id: uuid.UUID
    entity: str
    entity_id: str
    action: str
    changes: dict[str, Any]
    reason: str | None
    actor_email: str | None
    created_at: datetime


class Reason(ApiModel):
    reason: str = Field(min_length=3, max_length=2000)


# ── Task bank ───────────────────────────────────────────────────────────────────────────────────


class TaskVariable(ApiModel):
    """A placeholder `{name}` of the statement, filled with a random number from the range."""

    name: str
    min: float
    max: float
    step: float = Field(default=1, gt=0)

    @field_validator("name")
    @classmethod
    def _valid_name(cls, value: str) -> str:
        if not _VARIABLE_NAME.match(value):
            msg = "имя переменной: латиница, цифры и _, не с цифры"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        if self.min > self.max:
            msg = "min не может быть больше max"
            raise ValueError(msg)
        return self


class AdminTaskWrite(ApiModel):
    """A platform task with what the admin panel adds. Only the two auto-graded kinds."""

    kind: TaskKind
    title: str = Field(min_length=1, max_length=200)
    statement: str = Field(min_length=1, max_length=20_000)
    specializations: list[str] = Field(default_factory=list, max_length=20)
    grade: str | None = None
    # «Навык»: the topic the bank already groups tasks by.
    skill: str = Field(min_length=1, max_length=64)
    difficulty: TaskDifficulty = TaskDifficulty.MEDIUM
    variables: list[TaskVariable] = Field(default_factory=list, max_length=10)
    time_limit_minutes: int | None = Field(default=None, ge=1, le=240)
    # Kind-specific content in the format of the bank (`QuizPayload` / `CodePayload`).
    payload: dict[str, Any]

    @field_validator("kind")
    @classmethod
    def _auto_graded(cls, value: TaskKind) -> TaskKind:
        if value not in (TaskKind.QUIZ, TaskKind.CODE):
            msg = "в банке платформы два типа: тест (quiz) и код (code)"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _unique_variables(self) -> Self:
        names = [variable.name for variable in self.variables]
        if len(names) != len(set(names)):
            msg = "имена переменных повторяются"
            raise ValueError(msg)
        return self


class AdminTaskCreate(AdminTaskWrite):
    # A new task starts as a draft or goes live at once.
    status: TaskStatus = TaskStatus.DRAFT

    @field_validator("status")
    @classmethod
    def _initial(cls, value: TaskStatus) -> TaskStatus:
        if value not in (TaskStatus.DRAFT, TaskStatus.ACTIVE):
            msg = "новое задание — черновик или активное"
            raise ValueError(msg)
        return value


class AdminTaskRow(ApiModel):
    id: uuid.UUID
    title: str
    kind: TaskKind
    specializations: list[str]
    grade: str | None
    skill: str
    difficulty: TaskDifficulty
    status: TaskStatus
    updated_at: datetime


class AdminTaskDetail(AdminTaskRow):
    statement: str
    variables: list[TaskVariable]
    time_limit_minutes: int | None
    payload: dict[str, Any]
    created_at: datetime
    # Attempts that already included the task: then it can only be archived, not deleted.
    attempts: int
    can_delete: bool
    allowed_statuses: list[TaskStatus]
    # What the editor should fix although the task is saved, see `TaskRead.warnings`.
    warnings: list[str] = Field(default_factory=list)


class StatusChange(ApiModel):
    status: TaskStatus
    reason: str | None = Field(default=None, max_length=2000)


class PreviewRequest(ApiModel):
    statement: str = Field(min_length=1, max_length=20_000)
    variables: list[TaskVariable] = Field(default_factory=list, max_length=10)
    # Quiz options may hold placeholders too.
    options: list[str] = Field(default_factory=list, max_length=8)
    count: int = Field(default=3, ge=1, le=6)


class PreviewVariant(ApiModel):
    values: dict[str, float]
    statement: str
    options: list[str]


# ── Analytics snapshots ─────────────────────────────────────────────────────────────────────────

Block = Literal["tasks", "task_card", "platform", "employers"]


class AnalyticsFilters(ApiModel):
    period: AnalyticsPeriod = AnalyticsPeriod.QUARTER
    task_id: uuid.UUID | None = None


class SnapshotMeta(ApiModel):
    id: uuid.UUID
    block: str
    filters: dict[str, Any]
    computed_at: datetime
    duration_ms: int
    # The next recalculation of these filters is allowed from then.
    next_allowed_at: datetime


class SnapshotRead(ApiModel):
    """The latest stored result; `snapshot` is null until the first calculation."""

    snapshot: SnapshotMeta | None
    result: dict[str, Any] | None


class TaskAnalyticsPage(ApiModel):
    snapshot: SnapshotMeta | None
    summary: dict[str, Any] | None
    rules: dict[str, Any] | None
    items: list[dict[str, Any]]
    total: int
    page: int
    per_page: int
    pages: int


class EmployerSignalsPage(ApiModel):
    snapshot: SnapshotMeta | None
    summary: dict[str, Any] | None
    unavailable: list[str]
    items: list[dict[str, Any]]
    total: int
    page: int
    per_page: int
    pages: int


# ── Employers ───────────────────────────────────────────────────────────────────────────────────

EmployerAction = Literal["clear", "warn", "restrict", "block"]


class EmployerDecision(ApiModel):
    action: EmployerAction
    reason: str = Field(min_length=3, max_length=2000)
    # «Restrict»: invitations a day the company keeps.
    invite_limit: int | None = Field(default=None, ge=0, le=1000)

    @model_validator(mode="after")
    def _limit_for_restriction(self) -> Self:
        if self.action == "restrict" and self.invite_limit is None:
            msg = "для ограничения укажите лимит приглашений в сутки"
            raise ValueError(msg)
        return self


class EmployerCaseRead(ApiModel):
    status: EmployerCaseStatus
    invite_limit: int | None
    updated_at: datetime


class NamedCount(ApiModel):
    label: str
    count: int


class EmployerVacancyRow(ApiModel):
    id: uuid.UUID
    title: str
    specialization: str
    grade: str
    published_at: datetime | None
    created_at: datetime


class EmployerOutreachRow(ApiModel):
    kind: Literal["like", "invitation", "test"]
    candidate_id: uuid.UUID
    candidate_name: str
    status: str | None
    created_at: datetime


class EmployerCard(ApiModel):
    company_id: uuid.UUID
    name: str
    industry: str | None
    city: str | None
    website: str | None
    contact_email: str | None
    owner_email: str
    registered_at: datetime
    case: EmployerCaseRead | None
    verification: VerificationStatus | None
    banned: bool
    # The company's row of the latest signals snapshot (null if it had no activity then).
    signals: dict[str, Any] | None
    snapshot: SnapshotMeta | None
    vacancies: list[EmployerVacancyRow]
    outreach: list[EmployerOutreachRow]
    history: list[AuditEntryRead]


# ── Banlist ─────────────────────────────────────────────────────────────────────────────────────


class BanCreate(ApiModel):
    company_id: uuid.UUID | None = None
    company_name: str | None = Field(default=None, max_length=200)
    inn: str | None = None
    email: Annotated[str, Field(max_length=320)] | None = None
    email_domain: str | None = None
    reason: str = Field(min_length=3, max_length=2000)

    @field_validator("inn")
    @classmethod
    def _inn(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip()
        if not _INN.match(value):
            msg = "ИНН: 10 или 12 цифр"
            raise ValueError(msg)
        return value

    @field_validator("email")
    @classmethod
    def _email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            msg = "некорректный email"
            raise ValueError(msg)
        return value

    @field_validator("email_domain")
    @classmethod
    def _domain(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip().lower().removeprefix("@")
        if not _DOMAIN.match(value):
            msg = "некорректный домен, например example.ru"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _something_to_block(self) -> Self:
        if not any((self.company_id, self.inn, self.email, self.email_domain)):
            msg = "укажите компанию, ИНН, email или домен"
            raise ValueError(msg)
        return self


class BanRead(ApiModel):
    id: uuid.UUID
    company_id: uuid.UUID | None
    company_name: str | None
    inn: str | None
    email: str | None
    email_domain: str | None
    reason: str
    is_active: bool
    created_at: datetime
    created_by_email: str | None
    unbanned_at: datetime | None
    unbanned_by_email: str | None
    unban_reason: str | None


# ── Dictionaries and parameters ─────────────────────────────────────────────────────────────────


class SpecializationRead(ApiModel):
    code: str
    label: str
    is_archived: bool
    # False: a specialization only the admin panel knows; the bank does not accept it yet.
    in_platform: bool


class SpecializationCreate(ApiModel):
    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$")
    label: str = Field(min_length=1, max_length=200)


class SpecializationUpdate(ApiModel):
    label: str | None = Field(default=None, min_length=1, max_length=200)
    is_archived: bool | None = None


class GradeRead(ApiModel):
    code: str
    label: str
    base: str


class SkillRead(ApiModel):
    id: uuid.UUID
    specialization_code: str
    name: str
    is_archived: bool


class SkillCreate(ApiModel):
    specialization_code: str
    name: str = Field(min_length=1, max_length=64)


class SkillUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    is_archived: bool | None = None


class DictionariesRead(ApiModel):
    specializations: list[SpecializationRead]
    grades: list[GradeRead]
    skills: list[SkillRead]


class ParameterRead(ApiModel):
    key: str
    label: str
    value: int
    default: int
    minimum: int
    maximum: int
    unit: str
    updated_at: datetime | None


class HardcodedRead(ApiModel):
    parameter: str
    where: str


class ParametersRead(ApiModel):
    items: list[ParameterRead]
    hardcoded: list[HardcodedRead]


class ParameterWrite(ApiModel):
    value: int


# ── Company verification ────────────────────────────────────────────────────────────────────────


class CompanyDocumentRead(ApiModel):
    id: uuid.UUID
    filename: str
    size_bytes: int
    uploaded_at: datetime
    kind: Literal["pdf", "docx"] = "pdf"


class VerificationRead(ApiModel):
    """The employer's view: null status until the first document is uploaded."""

    status: VerificationStatus | None
    submitted_at: datetime | None
    decided_at: datetime | None
    # Shown to the employer when the request was rejected.
    reason: str | None
    documents: list[CompanyDocumentRead]


class VerificationRow(ApiModel):
    company_id: uuid.UUID
    company_name: str
    owner_email: str
    status: VerificationStatus
    submitted_at: datetime
    decided_at: datetime | None
    documents: int


class VerificationDetail(VerificationRow):
    industry: str | None
    city: str | None
    website: str | None
    contact_email: str | None
    decision_reason: str | None
    decided_by_email: str | None
    files: list[CompanyDocumentRead]
    history: list[AuditEntryRead]


class VerificationApprove(ApiModel):
    comment: str | None = Field(default=None, max_length=2000)
