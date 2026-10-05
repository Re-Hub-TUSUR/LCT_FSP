import uuid
from datetime import datetime

from pydantic import Field

from app.models.enums import Grade, ReactionKind, WorkFormat
from app.schemas.category import Category
from app.schemas.common import ApiModel, Page, SalaryRange


class CompanyRef(ApiModel):
    id: uuid.UUID
    name: str


class CompanyBrief(CompanyRef):
    """What a vacancy card shows about the employer."""

    industry: str | None
    city: str | None
    size: str | None


class VacancyRead(ApiModel):
    id: uuid.UUID
    title: str
    company: CompanyBrief
    category: Category
    stack: list[str]
    salary: SalaryRange
    work_format: WorkFormat
    # Office location; null for remote positions.
    city: str | None
    description: str
    # Null for a draft, which only its company sees.
    published_at: datetime | None


class VacancyMatch(ApiModel):
    """One card of the candidate's feed with the explanation of its position."""

    vacancy: VacancyRead
    # Fit to the candidate's profile, 0–1. Null when the feed is not personalised.
    match_score: float | None
    reasons: list[str]
    reaction: ReactionKind | None


class FeedBasis(ApiModel):
    """The profile data the vacancy feed is personalised by."""

    category: Category | None
    grade_verified: bool
    stack: list[str]
    work_formats: list[WorkFormat]
    city: str | None
    salary_expectation: int | None


class VacancyFeedPage(Page[VacancyMatch]):
    # False until the candidate has a category: then the feed is just the newest vacancies.
    personalized: bool
    basis: FeedBasis | None


class VacancyCreate(ApiModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=20)
    specialization: str
    grade: Grade
    stack: list[str] = Field(default_factory=list)
    salary: SalaryRange
    work_format: WorkFormat
