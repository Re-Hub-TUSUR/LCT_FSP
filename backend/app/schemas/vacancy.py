import uuid
from datetime import datetime
from typing import Literal, Self

from pydantic import Field, model_validator

from app.models.enums import (
    EmploymentType,
    FspDiscipline,
    FspResult,
    Grade,
    ReactionKind,
    VacancyBenefit,
    WorkFormat,
)
from app.schemas.category import Category
from app.schemas.common import ApiModel, Page, SalaryRange
from app.schemas.facets import OptionCount


class CompanyRef(ApiModel):
    id: uuid.UUID
    name: str


class CompanyBrief(CompanyRef):
    """What a vacancy card shows about the employer."""

    industry: str | None
    city: str | None
    size: str | None
    # An admin approved the Минцифры registry extract: the check mark next to the name.
    it_accredited: bool = False
    has_logo: bool = False


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
    # One grade or two neighbouring ones; `category` carries the first.
    grades: list[Grade] = Field(default_factory=list)
    # `stack` above is both lists together.
    stack_required: list[str] = Field(default_factory=list)
    stack_nice: list[str] = Field(default_factory=list)
    relocation_help: bool = False
    employment_types: list[EmploymentType] = Field(default_factory=list)
    benefits: list[VacancyBenefit] = Field(default_factory=list)
    # Only candidates whose grade a test confirmed.
    verified_grade_only: bool = True
    fsp_best_result: FspResult | None = None
    fsp_discipline: FspDiscipline | None = None
    # 0 = any, otherwise 1, 3 or 5 years and more.
    min_experience_years: int = 0


class VacancyMatch(ApiModel):
    """One card of the candidate's feed with the explanation of its position."""

    vacancy: VacancyRead
    # Fit to the candidate's profile, 0–1. Null when the feed is not personalised.
    match_score: float | None
    reasons: list[str]
    reaction: ReactionKind | None
    # Mutual interest: the candidate liked the vacancy and its recruiter liked the candidate.
    matched: bool = False


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


# profile: the candidate's specializations and grades, best fit first. free: everything, newest.
FeedMode = Literal["profile", "free"]


class VacancyFilterSet(ApiModel):
    """The candidate's feed filters. «Подбор по профилю» fills them in from the profile."""

    # The top of the vacancy's range reaches it.
    salary_min: int | None = None
    # Remote vacancies fit from anywhere; office and hybrid ones need one of `cities`, or help
    # with relocation when `relocation`.
    work_formats: list[WorkFormat] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    relocation: bool = False
    employment_types: list[EmploymentType] = Field(default_factory=list)
    # «Обязательно»: every technology is required. «Будет плюсом»: ranks higher, filters nothing.
    stack: list[str] = Field(default_factory=list)
    nice: list[str] = Field(default_factory=list)
    # Every condition is required.
    benefits: list[VacancyBenefit] = Field(default_factory=list)
    accredited: bool = False


VacancyRelaxationKind = Literal[
    "salary", "work_formats", "employment", "cities", "stack", "benefit", "accredited", "mode"
]


class VacancyRelaxation(ApiModel):
    """A filter to loosen when no vacancy matched, and how many vacancies that brings back."""

    kind: VacancyRelaxationKind
    # `salary`: the lowered minimum; `stack`: the technology to move to «nice to have»;
    # `benefit`: the condition to drop.
    value: str | None = None
    count: int


class VacancyFacets(ApiModel):
    """How many vacancies each filter option leaves, the other filters staying as they are."""

    # Vacancies of the mode (and the view) before the filters.
    total: int
    # Vacancies matching every filter: the feed's total.
    count: int
    # The option added to the ones chosen in its group.
    work_formats: list[OptionCount]
    employment_types: list[OptionCount]
    benefits: list[OptionCount]
    accredited: int
    # How many vacancies of the mode are in each city and ask for each technology.
    cities: list[OptionCount]
    stack: list[OptionCount]
    # Up to three; only when nothing matched.
    relaxations: list[VacancyRelaxation]


class VacancyFeedPresets(ApiModel):
    # False until the candidate has a category: only the free search is possible then.
    personalized: bool
    # «Подбор по профилю»: the filters the profile suggests and how many vacancies they leave.
    profile: VacancyFilterSet | None
    profile_count: int
    category: Category | None
    # «Свободный поиск»: every published vacancy of the view.
    free_count: int


_GRADE_ORDER = list(Grade)
MinExperience = Literal[0, 1, 3, 5]


class VacancyCreate(ApiModel):
    """The recruiter's vacancy form (ТЗ). Salary is RUB per month, net («на руки»)."""

    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=150, max_length=5000)
    specialization: str
    grades: list[Grade] = Field(min_length=1, max_length=2)
    stack_required: list[str] = Field(min_length=1, max_length=20)
    stack_nice: list[str] = Field(default_factory=list, max_length=20)
    salary: SalaryRange
    work_format: WorkFormat
    # Required for office and hybrid work.
    city: str | None = Field(default=None, max_length=100)
    relocation_help: bool = False
    employment_types: list[EmploymentType] = Field(min_length=1)
    verified_grade_only: bool = True
    fsp_best_result: FspResult | None = None
    fsp_discipline: FspDiscipline | None = None
    min_experience_years: MinExperience = 0
    benefits: list[VacancyBenefit] = Field(default_factory=list)

    @model_validator(mode="after")
    def _rules(self) -> Self:
        if len(self.grades) > 1:
            first, *_, last = sorted(_GRADE_ORDER.index(grade) for grade in self.grades)
            if last - first != 1:
                msg = "Можно выбрать один грейд или два соседних"
                raise ValueError(msg)
        if self.work_format != WorkFormat.REMOTE and not (self.city and self.city.strip()):
            msg = "Укажите город для офиса или гибрида"
            raise ValueError(msg)
        return self
