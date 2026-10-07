"""What every structured filter of the candidate search means.

The database engine and the facet counts evaluate these functions; the Elasticsearch query
(`app.search.query`) builds the same conditions, and `tests/test_search_elastic.py` checks that
both engines return the same candidates in the same order.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Literal, Protocol

from app.models import CandidateProfile
from app.models.enums import FspDiscipline, FspResult, Grade, WorkFormat
from app.search.base import CandidateSearchQuery
from app.services.matching import PRIZE_PLACES, as_utc, normalize_term

Group = Literal[
    "specialization",
    "grade",
    "verified",
    "fsp",
    "experience",
    "stack",
    "salary",
    "location",
    "employment",
    "status",
    "activity",
]
GROUPS: Final[tuple[Group, ...]] = (
    "specialization",
    "grade",
    "verified",
    "fsp",
    "experience",
    "stack",
    "salary",
    "location",
    "employment",
    "status",
    "activity",
)

RESULT_RANK: Final[dict[FspResult, int]] = {
    FspResult.PARTICIPANT: 0,
    FspResult.FINALIST: 1,
    FspResult.PRIZEWINNER: 2,
}
ANY_DISCIPLINE: Final = "any"


class _Achievement(Protocol):
    @property
    def discipline(self) -> FspDiscipline: ...

    @property
    def place(self) -> int | None: ...


def result_of(place: int | None) -> FspResult:
    """The registry keeps the place: none — took part, a prize place — prizewinner, else final."""
    if place is None:
        return FspResult.PARTICIPANT
    return FspResult.PRIZEWINNER if place <= PRIZE_PLACES else FspResult.FINALIST


def fsp_marks(achievements: Iterable[_Achievement]) -> frozenset[str]:
    """`discipline:result` for every result up to the one reached, also under `any`: one term
    answers «a result of at least X in discipline Y» in both engines."""
    marks: set[str] = set()
    for item in achievements:
        reached = RESULT_RANK[result_of(item.place)]
        for result, rank in RESULT_RANK.items():
            if rank <= reached:
                marks.add(f"{FspDiscipline(item.discipline).value}:{result.value}")
                marks.add(f"{ANY_DISCIPLINE}:{result.value}")
    return frozenset(marks)


def fsp_mark(query: CandidateSearchQuery) -> str:
    discipline = query.fsp_discipline.value if query.fsp_discipline else ANY_DISCIPLINE
    return f"{discipline}:{(query.fsp_result or FspResult.PARTICIPANT).value}"


def wants_fsp(query: CandidateSearchQuery) -> bool:
    return query.has_fsp is True or query.fsp_result is not None or query.fsp_discipline is not None


@dataclass(frozen=True, slots=True)
class FilterFacts:
    """A profile reduced to what the filters compare; text values are already normalised."""

    specialization: str | None
    grade: Grade | None
    verified: bool
    fsp_marks: frozenset[str]
    experience: int | None
    stack: frozenset[str]
    salary: int | None
    formats: frozenset[str]
    city: str | None
    relocation: bool
    employment: frozenset[str]
    status: str
    last_active: datetime | None

    @classmethod
    def of(cls, profile: CandidateProfile) -> "FilterFacts":
        """`profile.fsp_achievements` must be loaded."""
        return cls(
            specialization=profile.specialization,
            grade=profile.grade,
            verified=profile.assessment_score is not None,
            fsp_marks=fsp_marks(profile.fsp_achievements),
            experience=profile.experience_years,
            stack=frozenset(normalize_term(item) for item in profile.stack),
            salary=profile.salary_expectation,
            formats=frozenset(profile.work_formats),
            city=normalize_term(profile.city) if profile.city else None,
            relocation=profile.relocation_ready,
            employment=frozenset(profile.employment_types),
            status=profile.job_status.value,
            last_active=as_utc(profile.last_active_at) if profile.last_active_at else None,
        )


def check(group: Group, facts: FilterFacts, query: CandidateSearchQuery) -> bool:  # noqa: PLR0911 - one return per filter keeps the meaning readable
    match group:
        case "specialization":
            return not query.specializations or facts.specialization in query.specializations
        case "grade":
            return not query.grades or facts.grade in query.grades
        case "verified":
            return not query.verified_only or facts.verified
        case "fsp":
            if query.has_fsp is False:
                return not facts.fsp_marks
            return not wants_fsp(query) or fsp_mark(query) in facts.fsp_marks
        case "experience":
            minimum = query.experience_min
            return minimum is None or (facts.experience is not None and facts.experience >= minimum)
        case "stack":
            return all(normalize_term(item) in facts.stack for item in query.stack)
        case "salary":
            return _salary(facts.salary, query)
        case "location":
            return location_fits(facts, query)
        case "employment":
            wanted = {item.value for item in query.employment_types}
            return not wanted or bool(wanted & facts.employment)
        case "status":
            return not query.job_statuses or facts.status in {s.value for s in query.job_statuses}
        case "activity":
            since = query.active_since
            return since is None or (facts.last_active is not None and facts.last_active >= since)


def _salary(expectation: int | None, query: CandidateSearchQuery) -> bool:
    if expectation is None:
        return True
    above_min = query.salary_min is None or expectation >= query.salary_min
    return above_min and (query.salary_max is None or expectation <= query.salary_max)


def location_fits(facts: FilterFacts, query: CandidateSearchQuery) -> bool:
    """Remote work needs no city; office and hybrid need one of the cities (or readiness to
    move when relocation is counted in). Without formats only the city is checked."""
    cities = {normalize_term(city) for city in query.cities}
    city_ok = not cities or facts.city in cities or (query.include_relocation and facts.relocation)
    if not query.work_formats:
        return city_ok
    remote = WorkFormat.REMOTE in query.work_formats and WorkFormat.REMOTE.value in facts.formats
    onsite = any(
        fmt != WorkFormat.REMOTE and fmt.value in facts.formats for fmt in query.work_formats
    )
    return remote or (onsite and city_ok)


def failed_groups(facts: FilterFacts, query: CandidateSearchQuery) -> tuple[Group, ...]:
    return tuple(group for group in GROUPS if not check(group, facts, query))


def passes(facts: FilterFacts, query: CandidateSearchQuery) -> bool:
    return all(check(group, facts, query) for group in GROUPS)


def nice_matches(facts: FilterFacts, query: CandidateSearchQuery) -> int:
    """How many «nice to have» technologies the candidate has: they lift the candidate up."""
    return sum(term in facts.stack for term in dict.fromkeys(map(normalize_term, query.nice_stack)))
