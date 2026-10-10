import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import Field, model_validator

from app.models.enums import (
    AssessmentStatus,
    EmploymentType,
    FspDiscipline,
    FspEventKind,
    FspEventLevel,
    FspOutcome,
    FspParticipation,
    FspResult,
    FspSync,
    FspTitleKind,
    Grade,
    JobStatus,
    ReactionKind,
    WorkFormat,
)
from app.schemas.category import Category
from app.schemas.common import ApiModel, Page
from app.schemas.facets import OptionCount

_MONTH = r"^\d{4}-(0[1-9]|1[0-2])$"


class ExperienceEntry(ApiModel):
    """One job. Months are "YYYY-MM"; no end means the candidate still works there."""

    company: str = Field(min_length=1, max_length=200)
    position: str = Field(min_length=1, max_length=200)
    start: str = Field(pattern=_MONTH)
    end: str | None = Field(default=None, pattern=_MONTH)
    stack: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def _period(self) -> "ExperienceEntry":
        if self.end is not None and self.end < self.start:
            msg = "Окончание работы раньше начала"
            raise ValueError(msg)
        return self


class EducationEntry(ApiModel):
    institution: str = Field(min_length=1, max_length=300)
    specialty: str | None = Field(default=None, max_length=200)
    # Graduation year, or the expected one.
    year: int | None = Field(default=None, ge=1950, le=2100)


class FspAchievementRead(ApiModel):
    """A result confirmed by the FSP registry. It ranks the candidate, never sets the grade."""

    event_name: str
    event_kind: FspEventKind
    year: int
    # Null = took part without a place.
    place: int | None
    result: FspOutcome
    participation: FspParticipation
    team_name: str | None
    discipline: FspDiscipline
    level: FspEventLevel


class FspSportTitleRead(ApiModel):
    """Sport rank (разряд) or title (звание) in sport programming."""

    kind: FspTitleKind
    discipline: FspDiscipline
    awarded_year: int


class CandidateContacts(ApiModel):
    email: str
    phone: str | None
    telegram: str | None


class ResumeRead(ApiModel):
    """One profession profile. The priority resume is what employers and the feed see first."""

    id: uuid.UUID
    headline: str | None
    specialization: str | None
    stack: list[str]
    soft_skills: list[str]
    about: str | None
    experience_years: int | None
    is_primary: bool


class ResumeCreate(ApiModel):
    headline: str = Field(min_length=1, max_length=300)
    specialization: str = Field(min_length=1, max_length=64)
    stack: list[str] = Field(min_length=1, max_length=30)
    soft_skills: list[str] = Field(default_factory=list, max_length=20)
    about: str | None = Field(default=None, max_length=2000)
    experience_years: int = Field(ge=0, le=50)


class CandidateRead(ApiModel):
    id: uuid.UUID
    display_name: str
    headline: str | None
    about: str | None
    category: Category | None
    # False: the test was skipped and the grade in `category` is self-declared.
    grade_verified: bool
    # True: the grade was confirmed by a beta test and is provisional.
    grade_beta: bool = False
    assessment_score: float | None
    # Three states for the employer: passed, failed, or the test was never taken.
    assessment_status: AssessmentStatus
    stack: list[str]
    soft_skills: list[str]
    experience_years: int | None
    english_level: str | None
    city: str | None
    relocation_ready: bool
    work_formats: list[WorkFormat]
    salary_expectation: int | None
    # Empty list = no FSP history; must be handled explicitly (ТЗ, section 2).
    fsp_achievements: list[FspAchievementRead]
    fsp_titles: list[FspSportTitleRead] = Field(default_factory=list)
    fsp_linked: bool
    # Priority resume first, then the others.
    resumes: list[ResumeRead] = Field(default_factory=list)
    has_photo: bool = False
    job_status: JobStatus = JobStatus.OPEN
    employment_types: list[EmploymentType] = Field(default_factory=list)
    experience_entries: list[ExperienceEntry] = Field(default_factory=list)
    no_experience: bool = False
    education: list[EducationEntry] = Field(default_factory=list)
    github_url: str | None = None
    # 14–17 years old: the «до 18» mark. The birth date itself never reaches an employer.
    is_minor: bool = False
    # The owner's last sign-in, for the «активен за 30 дней» filter.
    last_active_at: datetime | None = None
    # Revealed only after the candidate accepted an invitation or applied (ТЗ 2.2, item 2).
    contacts: CandidateContacts | None
    # For an employer viewing one profile: mutual interest (the recruiter liked the candidate,
    # the candidate liked a vacancy of the company). Null where it is not computed.
    matched: bool | None = None


class CandidateMatch(ApiModel):
    """One card of the recruiter's feed with the explanation of its position."""

    candidate: CandidateRead
    # Fit to the selected vacancy, 0–1. Null when the search is not tied to a vacancy.
    match_score: float | None
    # Test result plus FSP results, 0–1: the order inside a category (ТЗ 2.1).
    profile_strength: float
    reasons: list[str]
    reaction: ReactionKind | None
    # Mutual interest: the recruiter liked the candidate, who liked a vacancy of the company.
    matched: bool = False


SearchEngine = Literal["elasticsearch", "database"]


class CandidateSearchPage(Page[CandidateMatch]):
    # Which engine answered: Elasticsearch, or the database fallback when it is unavailable.
    engine: SearchEngine


class CandidateFilterSet(ApiModel):
    """The recruiter's search filters. Selecting a vacancy fills them in from its requirements."""

    # Any of the listed specializations and grades.
    specializations: list[str] = Field(default_factory=list)
    grades: list[Grade] = Field(default_factory=list)
    verified_only: bool = False
    # False: no FSP results. True: some result, at least `fsp_result` in `fsp_discipline`.
    has_fsp: bool | None = None
    fsp_result: FspResult | None = None
    fsp_discipline: FspDiscipline | None = None
    experience_min: int | None = None
    # «Обязательно»: every technology is required. «Будет плюсом»: ranks higher, filters nobody.
    stack: list[str] = Field(default_factory=list)
    nice: list[str] = Field(default_factory=list)
    # Monthly net expectations; candidates without one are not excluded.
    salary_min: int | None = None
    salary_max: int | None = None
    # Remote work needs no city; office and hybrid need one of `cities`, or readiness to relocate
    # when `relocation`.
    work_formats: list[WorkFormat] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    relocation: bool = True
    employment_types: list[EmploymentType] = Field(default_factory=list)
    job_statuses: list[JobStatus] = Field(default_factory=list)
    # Signed in within this many days.
    active_days: int | None = None


CandidateRelaxationKind = Literal[
    "stack",
    "salary_max",
    "salary_min",
    "grades",
    "specializations",
    "verified",
    "fsp_result",
    "fsp_discipline",
    "fsp",
    "experience",
    "work_formats",
    "relocation",
    "cities",
    "employment",
    "job_statuses",
    "active",
]


class CandidateRelaxation(ApiModel):
    """A filter to loosen when nobody matched, and how many candidates that brings back."""

    kind: CandidateRelaxationKind
    # `stack`: the required technology to move to «nice to have».
    value: str | None = None
    count: int


class CandidateFacets(ApiModel):
    """How many candidates each filter option leaves, the other filters staying as they are."""

    # Candidates of the view (and of the text query) before the filters.
    total: int
    # Candidates matching every filter: the list's total.
    count: int
    # The option chosen alone in its group.
    specializations: list[OptionCount]
    grades: list[OptionCount]
    verified: int
    # «Есть результаты ФСП» switched on, then each best result and each discipline.
    fsp: int
    fsp_results: list[OptionCount]
    fsp_disciplines: list[OptionCount]
    # At least 1, 3 and 5 years of commercial experience.
    experience: list[OptionCount]
    work_formats: list[OptionCount]
    # Each city of the bank alone, without relocation; the most frequent first.
    cities: list[OptionCount]
    relocation: int
    employment_types: list[OptionCount]
    job_statuses: list[OptionCount]
    # Signed in within the last 30 days.
    active: int
    # Each technology of the bank: how many matching candidates know it, the most frequent first.
    stack: list[OptionCount]
    # Up to three; only when nobody matched.
    relaxations: list[CandidateRelaxation]


class VacancyPreset(ApiModel):
    """An own vacancy in the search's mode list with its requirements as filters."""

    vacancy_id: uuid.UUID
    title: str
    work_format: WorkFormat
    city: str | None
    salary_to: int
    published: bool
    filters: CandidateFilterSet
    # Candidates these filters leave.
    count: int


class CandidatePresets(ApiModel):
    # Free search: every candidate of the view.
    total: int
    vacancies: list[VacancyPreset]


class OwnCandidateRead(CandidateRead):
    """The candidate's own cabinet: includes the search switch and the FSP id they typed.

    `specialization` is kept even before a grade exists, so the resume form can reload it.
    Employers still see a category only after the test confirms a grade.
    """

    searching: bool
    fsp_member_id: str | None
    specialization: str | None
    birth_date: date | None = None
    profile_display_consent: bool = False
    fsp_sync: FspSync | None = None
    fsp_linked_at: datetime | None = None
    # Last successful import from the FSP registry.
    fsp_synced_at: datetime | None = None
    # Why the last import failed; null after a successful one.
    fsp_sync_error: str | None = None


class CandidateProfileUpdate(ApiModel):
    """Resume fields. The grade is never accepted here: only a passed test confirms it.

    Salaries are RUB per month, net («на руки»).
    """

    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    headline: str | None = Field(default=None, min_length=1, max_length=300)
    about: str | None = Field(default=None, max_length=2000)
    stack: list[str] | None = Field(default=None, max_length=30)
    soft_skills: list[str] | None = Field(default=None, max_length=20)
    experience_years: int | None = Field(default=None, ge=0, le=50)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    work_formats: list[WorkFormat] | None = None
    salary_expectation: int | None = Field(default=None, gt=0)
    phone: str | None = Field(default=None, max_length=32)
    telegram: str | None = Field(default=None, max_length=64)
    specialization: str | None = Field(default=None, min_length=1, max_length=64)
    relocation_ready: bool | None = None
    birth_date: date | None = None
    job_status: JobStatus | None = None
    employment_types: list[EmploymentType] | None = None
    experience_entries: list[ExperienceEntry] | None = Field(default=None, max_length=30)
    no_experience: bool | None = None
    education: list[EducationEntry] | None = Field(default=None, max_length=10)
    github_url: str | None = Field(default=None, max_length=300)
    profile_display_consent: bool | None = None
    fsp_sync: FspSync | None = None


class ResumeDraft(ApiModel):
    """Fields recognised in an uploaded resume. Nothing is saved: the candidate checks them."""

    display_name: str | None
    headline: str | None
    specialization: str | None
    city: str | None
    experience_years: int | None
    work_formats: list[WorkFormat]
    stack: list[str]
    soft_skills: list[str]
    about: str | None
    salary_expectation: int | None
    phone: str | None
    telegram: str | None
    # Portrait found in the file, base64 JPEG. The form uploads it together with the resume.
    photo: str | None = None


class CandidateSearchUpdate(ApiModel):
    """Either the old switch or the job status; the status wins when both are sent."""

    searching: bool | None = None
    job_status: JobStatus | None = None

    @model_validator(mode="after")
    def _one(self) -> "CandidateSearchUpdate":
        if self.searching is None and self.job_status is None:
            msg = "Укажите статус поиска"
            raise ValueError(msg)
        return self

    def status(self) -> JobStatus:
        if self.job_status is not None:
            return self.job_status
        return JobStatus.OPEN if self.searching else JobStatus.NOT_LOOKING


class FspAuthorizeRequest(ApiModel):
    # The SPA page FSP ID returns to; must be the configured callback.
    redirect_uri: str = Field(min_length=1, max_length=500)


class FspAuthorizeRead(ApiModel):
    """Where to send the browser: the FSP ID sign-in page with state, nonce and PKCE."""

    authorize_url: str


class FspLinkRequest(ApiModel):
    """What FSP ID appended to the callback URL."""

    code: str = Field(min_length=1, max_length=4096)
    state: str = Field(min_length=1, max_length=4096)
