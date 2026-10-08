"""Counts next to the recruiter's filter options and the ways out of an empty list.

Each count is what the list would show after that click (`app.services.facets`), computed with
the predicates of `app.search.filters`, so the counts agree with both search engines.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any, Final

from app.models import CandidateProfile
from app.models.enums import EmploymentType, FspDiscipline, FspResult, Grade, JobStatus, WorkFormat
from app.schemas.candidate import CandidateFacets, CandidateRelaxation, CandidateRelaxationKind
from app.schemas.facets import OptionCount
from app.search.base import CandidateSearchQuery
from app.search.filters import GROUPS, FilterFacts, Group, check, wants_fsp
from app.services.categories import SPECIALIZATIONS
from app.services.facets import FacetCounter, best_relaxations, ranked, spellings

# «Активен за последние 30 дней».
ACTIVE_DAYS: Final = 30
EXPERIENCE_STEPS: Final = (1, 3, 5)
# Profiles of people not looking for a job are hidden from employers: nobody to count.
LOOKING: Final = (JobStatus.ACTIVE, JobStatus.OPEN)

CandidateCounter = FacetCounter[FilterFacts, CandidateSearchQuery, Group]


def candidate_counter(
    profiles: Sequence[CandidateProfile], query: CandidateSearchQuery
) -> CandidateCounter:
    """`profiles` must have their achievements loaded."""
    return FacetCounter(
        [FilterFacts.of(profile) for profile in profiles], query, groups=GROUPS, check=check
    )


def candidate_facets(
    profiles: Sequence[CandidateProfile], query: CandidateSearchQuery, *, now: datetime
) -> CandidateFacets:
    """`profiles`: what the list starts from (the view and the text query), with achievements."""
    counter = candidate_counter(profiles, query)

    def with_(group: Group, **changes: Any) -> int:
        return counter.count_with(group, replace(query, **changes))

    def option(value: str, group: Group, **changes: Any) -> OptionCount:
        return OptionCount(value=value, count=with_(group, **changes))

    cities = [
        option(city, "location", cities=(city,), include_relocation=False)
        for city in spellings(profile.city for profile in profiles if profile.city).values()
    ]
    used = Counter(term for facts in counter.matching for term in facts.stack)
    known = spellings(item for profile in profiles for item in profile.stack)
    return CandidateFacets(
        total=len(profiles),
        count=counter.count,
        specializations=[
            option(code, "specialization", specializations=(code,)) for code in SPECIALIZATIONS
        ],
        grades=[option(grade.value, "grade", grades=(grade,)) for grade in Grade],
        verified=with_("verified", verified_only=True),
        fsp=with_("fsp", has_fsp=True),
        fsp_results=[
            option(result.value, "fsp", has_fsp=True, fsp_result=result) for result in FspResult
        ],
        fsp_disciplines=[
            option(discipline.value, "fsp", has_fsp=True, fsp_discipline=discipline)
            for discipline in FspDiscipline
        ],
        experience=[
            option(str(years), "experience", experience_min=years) for years in EXPERIENCE_STEPS
        ],
        work_formats=[option(fmt.value, "location", work_formats=(fmt,)) for fmt in WorkFormat],
        cities=sorted(cities, key=lambda item: (-item.count, item.value.casefold())),
        relocation=with_("location", include_relocation=True),
        employment_types=[
            option(kind.value, "employment", employment_types=(kind,)) for kind in EmploymentType
        ],
        job_statuses=[option(status.value, "status", job_statuses=(status,)) for status in LOOKING],
        active=with_("activity", active_since=now - timedelta(days=ACTIVE_DAYS)),
        stack=ranked(used, known),
        relaxations=candidate_relaxations(counter, query) if counter.count == 0 else [],
    )


def _only_remote(query: CandidateSearchQuery) -> bool:
    return set(query.work_formats) == {WorkFormat.REMOTE}


def candidate_relaxations(  # noqa: PLR0912 - one branch per filter, as the panel lists them
    counter: CandidateCounter, query: CandidateSearchQuery
) -> list[CandidateRelaxation]:
    """Single changes that bring candidates back, the most rewarding first."""
    options: list[CandidateRelaxation] = []

    def add(
        kind: CandidateRelaxationKind, group: Group, value: str | None = None, **changes: Any
    ) -> None:
        count = counter.count_with(group, replace(query, **changes))
        options.append(CandidateRelaxation(kind=kind, value=value, count=count))

    for item in query.stack:
        add("stack", "stack", item, stack=tuple(other for other in query.stack if other != item))
    if query.salary_max is not None:
        add("salary_max", "salary", salary_max=None)
    if query.salary_min is not None:
        add("salary_min", "salary", salary_min=None)
    if query.grades:
        add("grades", "grade", grades=())
    if query.specializations:
        add("specializations", "specialization", specializations=())
    if query.verified_only:
        add("verified", "verified", verified_only=False)
    if wants_fsp(query) or query.has_fsp is False:
        if query.fsp_result not in {None, FspResult.PARTICIPANT}:
            add("fsp_result", "fsp", fsp_result=None)
        if query.fsp_discipline is not None:
            add("fsp_discipline", "fsp", fsp_discipline=None)
        add("fsp", "fsp", has_fsp=None, fsp_result=None, fsp_discipline=None)
    if query.experience_min:
        add("experience", "experience", experience_min=None)
    if query.work_formats:
        add("work_formats", "location", work_formats=())
    if query.cities and not _only_remote(query):
        if not query.include_relocation:
            add("relocation", "location", include_relocation=True)
        add("cities", "location", cities=())
    if query.employment_types:
        add("employment", "employment", employment_types=())
    if query.job_statuses:
        add("job_statuses", "status", job_statuses=())
    if query.active_since is not None:
        add("active", "activity", active_since=None)
    return best_relaxations(options)
