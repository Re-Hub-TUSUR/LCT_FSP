import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from app.models.enums import (
    EmploymentType,
    FspDiscipline,
    FspResult,
    Grade,
    JobStatus,
    WorkFormat,
)
from app.schemas.candidate import SearchEngine
from app.services.matching import VacancyFacts

# relevance: fit to the vacancy when one is selected, otherwise profile strength (plus text match).
CandidateSort = Literal["relevance", "assessment", "salary", "experience"]


@dataclass(frozen=True, slots=True)
class CandidateSearchQuery:
    """Structured filters mean the same in every engine: see `app.search.filters`."""

    text: str | None = None
    # Any of the listed specializations / grades.
    specializations: tuple[str, ...] = ()
    grades: tuple[Grade, ...] = ()
    # Every listed technology is required.
    stack: tuple[str, ...] = ()
    # «Будет плюсом»: no filtering, the candidates with more of these go first (relevance only).
    nice_stack: tuple[str, ...] = ()
    # False: no FSP results at all. True: some result, narrowed by the two fields below.
    has_fsp: bool | None = None
    fsp_result: FspResult | None = None
    fsp_discipline: FspDiscipline | None = None
    verified_only: bool = False
    experience_min: int | None = None
    # Expectations inside the range; candidates without an expectation pass.
    salary_min: int | None = None
    salary_max: int | None = None
    # Any of the listed formats. Remote work needs no city; the others need one of `cities`
    # (or readiness to relocate when `include_relocation`).
    work_formats: tuple[WorkFormat, ...] = ()
    cities: tuple[str, ...] = ()
    # GeoNames ids. When set, the city filter uses these and ignores `cities`.
    city_ids: tuple[int, ...] = ()
    include_relocation: bool = True
    employment_types: tuple[EmploymentType, ...] = ()
    job_statuses: tuple[JobStatus, ...] = ()
    # Signed in since then.
    active_since: datetime | None = None
    # Hiring for this vacancy: rank by fit to it.
    vacancy: VacancyFacts | None = None
    # Favourites view: only these candidates.
    include_ids: tuple[uuid.UUID, ...] | None = None
    exclude_ids: tuple[uuid.UUID, ...] = ()
    sort: CandidateSort = "relevance"


@dataclass(frozen=True, slots=True)
class SearchHits:
    ids: list[uuid.UUID]
    total: int


class SearchUnavailableError(Exception):
    """The engine can't answer now; the caller falls back to the database engine."""


class CandidateSearchEngine(Protocol):
    name: SearchEngine

    async def search(self, query: CandidateSearchQuery, *, offset: int, limit: int) -> SearchHits:
        """Ordered ids of one page of visible, categorised candidates and the total count."""
        ...
