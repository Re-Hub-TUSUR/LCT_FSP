"""The recruiter's feed: search over visible, categorised candidates with explained ranking."""

import logging
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from typing import Final

from app.core.errors import ConflictError, NotFoundError
from app.dependencies.common import Pagination
from app.models import (
    CandidateProfile,
    CandidateReaction,
    Grade,
    ReactionKind,
    User,
    Vacancy,
    WorkFormat,
)
from app.models.enums import EmploymentType, FspResult
from app.repositories.candidate import CandidateRepository
from app.repositories.company import CompanyRepository
from app.repositories.reaction import ReactionRepository, ids_with
from app.repositories.vacancy import VacancyRepository
from app.schemas.candidate import (
    CandidateFacets,
    CandidateFilterSet,
    CandidateMatch,
    CandidatePresets,
    CandidateSearchPage,
    SearchEngine,
    VacancyPreset,
)
from app.schemas.reaction import FeedView, ReactionCounts
from app.search.base import CandidateSearchQuery, CandidateSort, SearchHits, SearchUnavailableError
from app.search.database import DatabaseCandidateSearch
from app.search.elastic import ElasticCandidateSearch, ElasticErrors, ElasticSearchState
from app.search.facets import candidate_facets
from app.search.filters import FilterFacts, passes
from app.services.cities import CityDirectory
from app.services.matching import CandidateFacts, VacancyFacts, candidate_reasons, fit
from app.services.presenters import candidate_read

logger = logging.getLogger(__name__)

# Facets count every candidate a text query finds, far beyond one page.
TEXT_MATCHES_LIMIT: Final = 10_000
# No filters: what a view and a text query narrow down.
_ANY: Final = CandidateSearchQuery()


@dataclass(frozen=True, slots=True)
class CandidateSearchParams:
    """What the recruiter asked for, before access checks and reactions are applied."""

    filters: CandidateFilterSet = field(default_factory=CandidateFilterSet)
    text: str | None = None
    vacancy_id: uuid.UUID | None = None
    view: FeedView = "all"
    sort: CandidateSort = "relevance"


def _terms(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value.strip() for value in values if value.strip()))


def candidate_query(
    filters: CandidateFilterSet, *, text: str | None, now: datetime
) -> CandidateSearchQuery:
    """The recruiter's filters as both search engines take them."""
    return CandidateSearchQuery(
        text=text.strip() if text and text.strip() else None,
        specializations=_terms(filters.specializations),
        grades=tuple(filters.grades),
        stack=_terms(filters.stack),
        nice_stack=_terms(filters.nice),
        has_fsp=filters.has_fsp,
        fsp_result=filters.fsp_result,
        fsp_discipline=filters.fsp_discipline,
        verified_only=filters.verified_only,
        experience_min=filters.experience_min or None,
        salary_min=filters.salary_min,
        salary_max=filters.salary_max,
        work_formats=tuple(filters.work_formats),
        cities=() if filters.city_ids else _terms(filters.cities),
        city_ids=tuple(filters.city_ids),
        include_relocation=filters.relocation,
        employment_types=tuple(filters.employment_types),
        job_statuses=tuple(filters.job_statuses),
        active_since=now - timedelta(days=filters.active_days) if filters.active_days else None,
    )


def vacancy_filters(vacancy: Vacancy) -> CandidateFilterSet:
    """A vacancy's requirements as the filters the search opens with when it is selected."""
    split = bool(vacancy.stack_required or vacancy.stack_nice)
    onsite = vacancy.work_format != WorkFormat.REMOTE
    wants_fsp = vacancy.fsp_best_result is not None or vacancy.fsp_discipline is not None
    return CandidateFilterSet(
        specializations=[vacancy.specialization],
        grades=[Grade(grade) for grade in vacancy.grades] or [vacancy.grade],
        verified_only=vacancy.verified_grade_only,
        has_fsp=True if wants_fsp else None,
        # Taking part is any result.
        fsp_result=None
        if vacancy.fsp_best_result == FspResult.PARTICIPANT
        else vacancy.fsp_best_result,
        fsp_discipline=vacancy.fsp_discipline,
        experience_min=vacancy.min_experience_years or None,
        stack=list(vacancy.stack_required),
        # A vacancy saved before the stack was split: its stack only ranks, it filters nobody out.
        nice=list(vacancy.stack_nice if split else vacancy.stack),
        salary_max=vacancy.salary_to,
        work_formats=[vacancy.work_format],
        city_ids=[vacancy.city_id] if onsite and vacancy.city_id else [],
        cities=[vacancy.city] if onsite and vacancy.city else [],
        employment_types=[EmploymentType(kind) for kind in vacancy.employment_types],
    )


@dataclass(frozen=True, slots=True)
class _Scope:
    """The recruiter's own decisions and which candidates a view lists because of them."""

    view: FeedView
    reactions: dict[uuid.UUID, CandidateReaction]
    matched: set[uuid.UUID]

    def apply(self, query: CandidateSearchQuery) -> CandidateSearchQuery:
        if self.view == "liked":
            return replace(query, include_ids=ids_with(self.reactions, (ReactionKind.LIKE,)))
        if self.view == "skipped":
            return replace(query, include_ids=ids_with(self.reactions, (ReactionKind.SKIP,)))
        if self.view == "matched":
            return replace(query, include_ids=tuple(self.matched))
        # The feed hides skipped candidates; the swipe deck hides everyone already decided on.
        hidden = (ReactionKind.SKIP,) if self.view == "all" else tuple(ReactionKind)
        return replace(query, exclude_ids=ids_with(self.reactions, hidden))


class CandidateSearchService:
    def __init__(
        self,
        candidates: CandidateRepository,
        vacancies: VacancyRepository,
        companies: CompanyRepository,
        reactions: ReactionRepository,
        elastic: ElasticSearchState | None,
        *,
        cities: CityDirectory | None = None,
    ) -> None:
        self._candidates = candidates
        self._vacancies = vacancies
        self._companies = companies
        self._reactions = reactions
        self._elastic = elastic
        self._cities = cities

    async def search(
        self,
        user: User,
        params: CandidateSearchParams,
        pagination: Pagination,
        *,
        now: datetime | None = None,
    ) -> CandidateSearchPage:
        await self._require_company(user)
        vacancy = await self._own_vacancy(user, params.vacancy_id)
        scope = await self._scope(user, params.view)
        query = await self._query(params.filters, text=params.text, now=now or datetime.now(UTC))
        query = replace(scope.apply(query), vacancy=vacancy, sort=params.sort)

        engine, hits = await self._run(query, offset=pagination.offset, limit=pagination.per_page)
        profiles = await self._candidates.by_ids(hits.ids)
        items = []
        for candidate_id in hits.ids:
            profile = profiles.get(candidate_id)
            if profile is None:  # deleted after indexing
                continue
            facts = CandidateFacts.of(profile)
            result = fit(facts, vacancy, bonus=facts.strength) if vacancy else None
            reaction = scope.reactions.get(candidate_id)
            items.append(
                CandidateMatch(
                    candidate=candidate_read(profile),
                    match_score=result.score if result else None,
                    profile_strength=facts.strength,
                    reasons=candidate_reasons(
                        facts, result, vacancy=vacancy, stack_filter=query.stack + query.nice_stack
                    ),
                    reaction=reaction.kind if reaction else None,
                    matched=candidate_id in scope.matched,
                )
            )
        return CandidateSearchPage.build(
            items,
            total=hits.total,
            page=pagination.page,
            per_page=pagination.per_page,
            engine=engine,
        )

    async def facets(
        self, user: User, params: CandidateSearchParams, *, now: datetime | None = None
    ) -> CandidateFacets:
        """Counts next to every filter option of the search with these parameters."""
        await self._require_company(user)
        now = now or datetime.now(UTC)
        scope = await self._scope(user, params.view)
        query = scope.apply(await self._query(params.filters, text=params.text, now=now))
        return candidate_facets(await self._base(query), query, now=now)

    async def presets(
        self, user: User, *, view: FeedView = "all", now: datetime | None = None
    ) -> CandidatePresets:
        """The search's modes: free search and every own vacancy with its filters filled in."""
        now = now or datetime.now(UTC)
        company = await self._companies.get_by_owner(user.id)
        rows = await self._vacancies.for_company(company.id) if company else []
        scope = await self._scope(user, view)
        facts = [FilterFacts.of(profile) for profile in await self._base(scope.apply(_ANY))]
        presets = []
        for vacancy, _ in rows:
            filters = await self._resolve_cities(vacancy_filters(vacancy))
            query = candidate_query(filters, text=None, now=now)
            presets.append(
                VacancyPreset(
                    vacancy_id=vacancy.id,
                    title=vacancy.title,
                    work_format=vacancy.work_format,
                    city=vacancy.city,
                    salary_to=vacancy.salary_to,
                    published=vacancy.published_at is not None,
                    filters=filters,
                    count=sum(passes(item, query) for item in facts),
                )
            )
        return CandidatePresets(total=len(facts), vacancies=presets)

    async def matching_ids(
        self,
        user: User,
        searches: Sequence[CandidateSearchParams],
        *,
        now: datetime | None = None,
    ) -> list[set[uuid.UUID]]:
        """The candidates each search finds now, as the feed shows them (skipped ones hidden)."""
        now = now or datetime.now(UTC)
        scope = await self._scope(user, "all")
        plain: list[tuple[uuid.UUID, FilterFacts]] | None = None
        found = []
        for params in searches:
            query = scope.apply(await self._query(params.filters, text=params.text, now=now))
            if query.text is None:
                if plain is None:
                    plain = [(p.id, FilterFacts.of(p)) for p in await self._base(query)]
                facts = plain
            else:
                facts = [(p.id, FilterFacts.of(p)) for p in await self._base(query)]
            found.append({candidate_id for candidate_id, item in facts if passes(item, query)})
        return found

    async def check_vacancy(self, user: User, vacancy_id: uuid.UUID) -> None:
        """Only an own vacancy may be searched for."""
        await self._own_vacancy(user, vacancy_id)

    async def counts(self, user: User) -> ReactionCounts:
        """Sizes of the lists `liked`, `matched` and `skipped` as the search would show them."""
        reactions = await self._reactions.for_candidates(user.id)
        matched = await self._matched(user)

        async def shown(ids: tuple[uuid.UUID, ...]) -> int:
            # Hidden and uncategorised profiles never appear in a list, so they do not count.
            return len(await self._candidates.searchable(include_ids=ids)) if ids else 0

        return ReactionCounts(
            liked=await shown(ids_with(reactions, (ReactionKind.LIKE,))),
            matched=await shown(tuple(matched)),
            skipped=await shown(ids_with(reactions, (ReactionKind.SKIP,))),
        )

    async def _query(
        self, filters: CandidateFilterSet, *, text: str | None, now: datetime
    ) -> CandidateSearchQuery:
        return candidate_query(await self._resolve_cities(filters), text=text, now=now)

    async def _resolve_cities(self, filters: CandidateFilterSet) -> CandidateFilterSet:
        """A typed city name becomes the places it names. An unknown name matches nobody."""
        if filters.city_ids or not filters.cities or self._cities is None:
            return filters
        ids = await self._cities.filter_ids(filters.cities)
        return filters.model_copy(update={"city_ids": ids or [-1], "cities": []})

    async def _require_company(self, user: User) -> None:
        """The candidate bank opens to a company, not to anyone who ticked «работодатель»."""
        if await self._companies.get_by_owner(user.id) is None:
            raise ConflictError("Сначала заполните профиль компании")

    async def _scope(self, user: User, view: FeedView) -> _Scope:
        return _Scope(
            view, await self._reactions.for_candidates(user.id), await self._matched(user)
        )

    async def _matched(self, user: User) -> set[uuid.UUID]:
        company = await self._companies.get_by_owner(user.id)
        if company is None:
            return set()
        return await self._reactions.matched_candidate_ids(
            recruiter_id=user.id, company_id=company.id
        )

    async def _own_vacancy(self, user: User, vacancy_id: uuid.UUID | None) -> VacancyFacts | None:
        """Hiring for a vacancy is only possible for the company's own vacancies."""
        if vacancy_id is None:
            return None
        row = await self._vacancies.get(vacancy_id)
        if row is None or row[1].owner_id != user.id:
            raise NotFoundError("Вакансия не найдена")
        return VacancyFacts.of(row[0])

    async def _base(self, query: CandidateSearchQuery) -> list[CandidateProfile]:
        """Candidates of the view that match the text query, whatever the filters say."""
        if query.text is None:
            profiles = await self._candidates.searchable(
                include_ids=query.include_ids, exclude_ids=query.exclude_ids
            )
            return list(profiles)
        text_only = replace(
            _ANY, text=query.text, include_ids=query.include_ids, exclude_ids=query.exclude_ids
        )
        _, hits = await self._run(text_only, offset=0, limit=TEXT_MATCHES_LIMIT)
        found = await self._candidates.by_ids(hits.ids)
        return [found[candidate_id] for candidate_id in hits.ids if candidate_id in found]

    async def _run(
        self, query: CandidateSearchQuery, *, offset: int, limit: int
    ) -> tuple[SearchEngine, SearchHits]:
        window = {"offset": offset, "limit": limit}
        if self._elastic is not None and await self._elastic.ready(self._candidates.all):
            try:
                await self._elastic.sync(self._candidates.updated_since)
                hits = await ElasticCandidateSearch(self._elastic.index).search(query, **window)
            except (SearchUnavailableError, *ElasticErrors) as exc:
                self._elastic.mark_unavailable()
                logger.warning("Elasticsearch search failed, using the database: %s", exc)
            else:
                return "elasticsearch", hits
        return "database", await DatabaseCandidateSearch(self._candidates).search(query, **window)
