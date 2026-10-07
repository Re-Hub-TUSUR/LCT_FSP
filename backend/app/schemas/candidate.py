import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import Field, model_validator

from app.models.enums import (
    AssessmentStatus,
    EmploymentType,
    FspDiscipline,
    FspEventLevel,
    FspSync,
    JobStatus,
    ReactionKind,
    WorkFormat,
)
from app.schemas.category import Category
from app.schemas.common import ApiModel, Page

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
    event_name: str
    year: int
    # Null = took part without a prize place.
    place: int | None
    discipline: FspDiscipline
    level: FspEventLevel


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


class FspLinkRequest(ApiModel):
    fsp_member_id: str = Field(min_length=1, max_length=64)
