import uuid
from dataclasses import dataclass
from typing import Literal, Protocol

from app.models import Grade, WorkFormat
from app.schemas.candidate import SearchEngine
from app.services.matching import VacancyFacts

# relevance: fit to the vacancy when one is selected, otherwise profile strength (plus text match).
CandidateSort = Literal["relevance", "assessment", "salary", "experience"]


@dataclass(frozen=True, slots=True)
class CandidateSearchQuery:
    text: str | None = None
    specialization: str | None = None
    grades: tuple[Grade, ...] = ()
    # Every listed technology is required.
    stack: tuple[str, ...] = ()
    has_fsp: bool | None = None
    verified_only: bool = False
    # Any of the listed formats.
    work_formats: tuple[WorkFormat, ...] = ()
    # Lives in the city or is ready to relocate.
    city: str | None = None
    # Budget: expectation not above it (candidates without an expectation pass).
    salary_max: int | None = None
    experience_min: int | None = None
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
