"""Typed view of `data/*.json` plus the invariants the loader and the feeds rely on."""

import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Annotated, Final, Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.enums import (
    FspDiscipline,
    FspEventKind,
    FspEventLevel,
    FspOutcome,
    FspParticipation,
    FspTitleKind,
    Grade,
    WorkFormat,
)
from app.services.categories import SPECIALIZATIONS

DATA_DIR: Final = Path(__file__).parent / "data"
DATASETS: Final = ("companies", "vacancies", "candidates")

# Dates are relative to the moment of loading, so the demo never looks stale.
DaysAgo = Annotated[int, Field(ge=0, le=3650)]


class Fixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _known_specialization(specialization: str) -> None:
    if specialization not in SPECIALIZATIONS:
        msg = f"unknown specialization {specialization!r}"
        raise ValueError(msg)


class FspAchievementFixture(Fixture):
    """One record of the emulated FSP registry; `id` is the registry's id of the result."""

    id: str = Field(min_length=1, max_length=64)
    event_name: str = Field(min_length=1, max_length=300)
    event_kind: FspEventKind
    discipline: FspDiscipline
    level: FspEventLevel
    year: int = Field(ge=2000, le=2100)
    place: int | None = Field(gt=0)
    result: FspOutcome
    participation: FspParticipation
    team_name: str | None = Field(max_length=200)

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.result != FspOutcome.from_place(self.place):
            msg = f"{self.id}: result {self.result} does not match place {self.place}"
            raise ValueError(msg)
        if (self.participation == FspParticipation.TEAM) != (self.team_name is not None):
            msg = f"{self.id}: only team results name a team"
            raise ValueError(msg)
        return self


class FspTitleFixture(Fixture):
    id: str = Field(min_length=1, max_length=64)
    kind: FspTitleKind
    discipline: FspDiscipline
    awarded_year: int = Field(ge=1990, le=2100)


class CandidateFixture(Fixture):
    key: str
    # Generator track, e.g. "go-backend": ground truth for evaluating the matching. Not stored.
    track: str
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=200)
    headline: str = Field(min_length=1, max_length=300)
    about: str
    specialization: str
    grade: Grade
    experience_years: int = Field(ge=0, le=60)
    stack: list[str] = Field(min_length=1)
    soft_skills: list[str]
    english_level: str | None = Field(pattern=r"^[ABC][12]$")
    city: str = Field(max_length=100)
    relocation_ready: bool
    work_formats: list[WorkFormat] = Field(min_length=1)
    salary_expectation: int = Field(gt=0)
    assessment_score: float | None = Field(ge=0, le=100)
    assessed_days_ago: DaysAgo | None
    registered_days_ago: DaysAgo
    fsp_member_id: str | None = Field(max_length=64)
    fsp_achievements: list[FspAchievementFixture]
    fsp_titles: list[FspTitleFixture]
    phone: str | None = Field(max_length=32)
    telegram: str | None = Field(max_length=64)
    is_visible_to_employers: bool

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        _known_specialization(self.specialization)
        if (self.assessment_score is None) != (self.assessed_days_ago is None):
            msg = f"{self.key}: assessment score and date go together"
            raise ValueError(msg)
        if (self.fsp_achievements or self.fsp_titles) and self.fsp_member_id is None:
            msg = f"{self.key}: FSP results require an FSP ID"
            raise ValueError(msg)
        return self


class CompanyFixture(Fixture):
    key: str
    owner_email: EmailStr
    name: str = Field(min_length=1, max_length=200)
    industry: str = Field(max_length=200)
    city: str = Field(max_length=100)
    size: str = Field(max_length=16)
    description: str
    website: str = Field(pattern=r"^https://", max_length=500)
    contact_email: EmailStr
    registered_days_ago: DaysAgo


class VacancyFixture(Fixture):
    key: str
    # Generator track, see `CandidateFixture.track`. Not stored.
    track: str
    company_key: str
    title: str = Field(min_length=3, max_length=200)
    specialization: str
    grade: Grade
    stack: list[str] = Field(min_length=1)
    salary_from: int = Field(gt=0)
    salary_to: int = Field(gt=0)
    work_format: WorkFormat
    city: str | None = Field(max_length=100)
    description: str = Field(min_length=20)
    # None = draft.
    published_days_ago: DaysAgo | None

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        _known_specialization(self.specialization)
        if self.salary_from > self.salary_to:
            msg = f"{self.key}: salary_from exceeds salary_to"
            raise ValueError(msg)
        if (self.work_format == WorkFormat.REMOTE) != (self.city is None):
            msg = f"{self.key}: only remote vacancies have no city"
            raise ValueError(msg)
        return self


def _unique(values: Iterable[str | None], what: str) -> None:
    repeated = [value for value, count in Counter(values).items() if value and count > 1]
    if repeated:
        msg = f"duplicate {what}: {', '.join(sorted(repeated))}"
        raise ValueError(msg)


class SeedData(Fixture):
    companies: list[CompanyFixture]
    vacancies: list[VacancyFixture]
    candidates: list[CandidateFixture]

    @model_validator(mode="after")
    def _references(self) -> Self:
        _unique((company.key for company in self.companies), "company keys")
        _unique((vacancy.key for vacancy in self.vacancies), "vacancy keys")
        _unique((candidate.key for candidate in self.candidates), "candidate keys")
        emails = [company.owner_email for company in self.companies]
        emails += [candidate.email for candidate in self.candidates]
        _unique(emails, "account emails")
        _unique((candidate.fsp_member_id for candidate in self.candidates), "FSP IDs")

        companies = {company.key for company in self.companies}
        orphans = [
            vacancy.key for vacancy in self.vacancies if vacancy.company_key not in companies
        ]
        if orphans:
            msg = f"vacancies of unknown companies: {', '.join(orphans)}"
            raise ValueError(msg)
        return self


def load_seed_data(data_dir: Path = DATA_DIR) -> SeedData:
    return SeedData.model_validate(
        {name: json.loads((data_dir / f"{name}.json").read_text("utf-8")) for name in DATASETS}
    )
