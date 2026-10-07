"""What every filter of the candidate's vacancy feed means, and the counts next to its options.

The feed is ranked in Python by the fit to the profile, so the filters run in Python as well.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any, Final, Literal, Self

from app.models import CandidateProfile, Company, Vacancy, WorkFormat
from app.models.enums import EmploymentType, VacancyBenefit
from app.repositories.vacancy import VacancyRow
from app.schemas.facets import OptionCount
from app.schemas.vacancy import (
    VacancyFacets,
    VacancyFilterSet,
    VacancyRelaxation,
    VacancyRelaxationKind,
)
from app.services.facets import FacetCounter, best_relaxations, ranked, spellings
from app.services.matching import normalize_term

VacancyGroup = Literal["mode", "salary", "location", "employment", "stack", "conditions"]
VACANCY_GROUPS: Final[tuple[VacancyGroup, ...]] = (
    "mode",
    "salary",
    "location",
    "employment",
    "stack",
    "conditions",
)

# «Снизить зарплату до …» offers the minimum lowered by this much.
SALARY_STEP: Final = 30_000


@dataclass(frozen=True, slots=True)
class ProfileScope:
    """«Подбор по профилю»: the candidate's specializations and the grades around their own."""

    specializations: frozenset[str]
    grades: frozenset[str]


@dataclass(frozen=True, slots=True)
class VacancyQuery:
    # None: free search over every published vacancy.
    scope: ProfileScope | None = None
    salary_min: int | None = None
    work_formats: tuple[WorkFormat, ...] = ()
    cities: tuple[str, ...] = ()
    relocation: bool = False
    employment_types: tuple[EmploymentType, ...] = ()
    stack: tuple[str, ...] = ()
    nice_stack: tuple[str, ...] = ()
    benefits: tuple[VacancyBenefit, ...] = ()
    accredited: bool = False


def _terms(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value.strip() for value in values if value.strip()))


def vacancy_query(filters: VacancyFilterSet, scope: ProfileScope | None) -> VacancyQuery:
    return VacancyQuery(
        scope=scope,
        salary_min=filters.salary_min,
        work_formats=tuple(filters.work_formats),
        cities=_terms(filters.cities),
        relocation=filters.relocation,
        employment_types=tuple(filters.employment_types),
        stack=_terms(filters.stack),
        nice_stack=_terms(filters.nice),
        benefits=tuple(filters.benefits),
        accredited=filters.accredited,
    )


def profile_filters(profile: CandidateProfile) -> VacancyFilterSet:
    """What «Подбор по профилю» fills in: the profile's expectations, formats, employment and
    city; its stack only lifts the vacancies asking for it."""
    return VacancyFilterSet(
        salary_min=profile.salary_expectation,
        work_formats=[WorkFormat(value) for value in profile.work_formats],
        # Ready to move: every city.
        cities=[profile.city] if profile.city and not profile.relocation_ready else [],
        employment_types=[EmploymentType(value) for value in profile.employment_types],
        nice=list(profile.stack),
    )


@dataclass(frozen=True, slots=True)
class VacancyFilterFacts:
    """A vacancy reduced to what the filters compare; text values are already normalised."""

    specialization: str
    grades: frozenset[str]
    salary_to: int
    work_format: WorkFormat
    city: str | None
    relocation_help: bool
    employment: frozenset[str]
    stack: frozenset[str]
    benefits: frozenset[str]
    accredited: bool

    @classmethod
    def of(cls, vacancy: Vacancy, company: Company) -> Self:
        technologies = (*vacancy.stack, *vacancy.stack_required, *vacancy.stack_nice)
        return cls(
            specialization=vacancy.specialization,
            grades=frozenset(vacancy.grades or [vacancy.grade.value]),
            salary_to=vacancy.salary_to,
            work_format=vacancy.work_format,
            city=normalize_term(vacancy.city) if vacancy.city else None,
            relocation_help=vacancy.relocation_help,
            employment=frozenset(vacancy.employment_types),
            stack=frozenset(normalize_term(item) for item in technologies),
            benefits=frozenset(vacancy.benefits),
            accredited=company.it_accredited,
        )


def check(group: VacancyGroup, facts: VacancyFilterFacts, query: VacancyQuery) -> bool:
    match group:
        case "mode":
            scope = query.scope
            return scope is None or (
                facts.specialization in scope.specializations
                and not facts.grades.isdisjoint(scope.grades)
            )
        case "salary":
            return query.salary_min is None or facts.salary_to >= query.salary_min
        case "location":
            return location_fits(facts, query)
        case "employment":
            wanted = {kind.value for kind in query.employment_types}
            return not wanted or not wanted.isdisjoint(facts.employment)
        case "stack":
            return all(normalize_term(item) in facts.stack for item in query.stack)
        case "conditions":
            benefits = all(benefit.value in facts.benefits for benefit in query.benefits)
            return benefits and (not query.accredited or facts.accredited)


def location_fits(facts: VacancyFilterFacts, query: VacancyQuery) -> bool:
    """A remote vacancy fits from anywhere; office and hybrid ones need one of the cities, or
    help with relocation when `relocation`."""
    if query.work_formats and facts.work_format not in query.work_formats:
        return False
    if facts.work_format == WorkFormat.REMOTE or not query.cities:
        return True
    cities = {normalize_term(city) for city in query.cities}
    return facts.city in cities or (query.relocation and facts.relocation_help)


def passes(facts: VacancyFilterFacts, query: VacancyQuery) -> bool:
    return all(check(group, facts, query) for group in VACANCY_GROUPS)


def nice_matches(facts: VacancyFilterFacts, query: VacancyQuery) -> int:
    """How many «nice to have» technologies the vacancy asks for: they lift it up."""
    return sum(term in facts.stack for term in dict.fromkeys(map(normalize_term, query.nice_stack)))


def _with[T](values: tuple[T, ...], value: T) -> tuple[T, ...]:
    return values if value in values else (*values, value)


VacancyCounter = FacetCounter[VacancyFilterFacts, VacancyQuery, VacancyGroup]


def vacancy_facets(rows: Sequence[VacancyRow], query: VacancyQuery) -> VacancyFacets:
    """`rows`: the vacancies the feed starts from (the view), before any filter."""
    facts = [VacancyFilterFacts.of(vacancy, company) for vacancy, company in rows]
    counter = FacetCounter(facts, query, groups=VACANCY_GROUPS, check=check)

    def added(group: VacancyGroup, **changes: Any) -> int:
        return counter.count_with(group, replace(query, **changes))

    in_mode = [
        (vacancy, item)
        for (vacancy, _), item in zip(rows, facts, strict=True)
        if check("mode", item, query)
    ]
    cities = Counter(item.city for _, item in in_mode if item.city)
    stack = Counter(term for _, item in in_mode for term in item.stack)
    return VacancyFacets(
        total=len(in_mode),
        count=counter.count,
        work_formats=[
            OptionCount(
                value=fmt.value,
                count=added("location", work_formats=_with(query.work_formats, fmt)),
            )
            for fmt in WorkFormat
        ],
        employment_types=[
            OptionCount(
                value=kind.value,
                count=added("employment", employment_types=_with(query.employment_types, kind)),
            )
            for kind in EmploymentType
        ],
        benefits=[
            OptionCount(
                value=benefit.value,
                count=added("conditions", benefits=_with(query.benefits, benefit)),
            )
            for benefit in VacancyBenefit
        ],
        accredited=added("conditions", accredited=True),
        cities=ranked(cities, spellings(v.city for v, _ in in_mode if v.city)),
        stack=ranked(
            stack,
            spellings(
                item
                for vacancy, _ in in_mode
                for item in (*vacancy.stack, *vacancy.stack_required, *vacancy.stack_nice)
            ),
        ),
        relaxations=vacancy_relaxations(counter, query) if counter.count == 0 else [],
    )


def vacancy_relaxations(counter: VacancyCounter, query: VacancyQuery) -> list[VacancyRelaxation]:
    """Single changes that bring vacancies back, the most rewarding first."""
    options: list[VacancyRelaxation] = []

    def add(
        kind: VacancyRelaxationKind, group: VacancyGroup, value: str | None = None, **changes: Any
    ) -> None:
        count = counter.count_with(group, replace(query, **changes))
        options.append(VacancyRelaxation(kind=kind, value=value, count=count))

    if query.salary_min:
        lowered = max(query.salary_min - SALARY_STEP, 0)
        add("salary", "salary", str(lowered), salary_min=lowered or None)
    if query.work_formats:
        add("work_formats", "location", work_formats=())
    if query.employment_types:
        add("employment", "employment", employment_types=())
    if query.cities:
        add("cities", "location", cities=())
    for item in query.stack:
        add("stack", "stack", item, stack=tuple(other for other in query.stack if other != item))
    for benefit in query.benefits:
        rest = tuple(other for other in query.benefits if other != benefit)
        add("benefit", "conditions", benefit.value, benefits=rest)
    if query.accredited:
        add("accredited", "conditions", accredited=False)
    if query.scope is not None:
        add("mode", "mode", scope=None)
    return best_relaxations(options)
