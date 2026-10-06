"""The recruiter's feed: search over visible, categorised candidates with explained ranking."""

import logging
import uuid
from dataclasses import dataclass, replace

from app.core.errors import NotFoundError
from app.dependencies.common import Pagination
from app.models import CandidateReaction, Grade, ReactionKind, User, WorkFormat
from app.repositories.candidate import CandidateRepository
from app.repositories.company import CompanyRepository
from app.repositories.reaction import ReactionRepository, ids_with
from app.repositories.vacancy import VacancyRepository
from app.schemas.candidate import CandidateMatch, CandidateSearchPage, SearchEngine
from app.schemas.reaction import FeedView
from app.search.base import CandidateSearchQuery, CandidateSort, SearchHits, SearchUnavailableError
from app.search.database import DatabaseCandidateSearch
from app.search.elastic import ElasticCandidateSearch, ElasticErrors, ElasticSearchState
from app.services.matching import CandidateFacts, VacancyFacts, candidate_reasons, fit
from app.services.presenters import candidate_read

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CandidateSearchParams:
    """What the recruiter asked for, before access checks and reactions are applied."""

    text: str | None = None
    specialization: str | None = None
    grades: tuple[Grade, ...] = ()
    stack: tuple[str, ...] = ()
    has_fsp: bool | None = None
    verified_only: bool = False
    work_formats: tuple[WorkFormat, ...] = ()
    city: str | None = None
    salary_max: int | None = None
    experience_min: int | None = None
    vacancy_id: uuid.UUID | None = None
    view: FeedView = "all"
    sort: CandidateSort = "relevance"


class CandidateSearchService:
    def __init__(
        self,
        candidates: CandidateRepository,
        vacancies: VacancyRepository,
        companies: CompanyRepository,
        reactions: ReactionRepository,
        elastic: ElasticSearchState | None,
    ) -> None:
        self._candidates = candidates
        self._vacancies = vacancies
        self._companies = companies
        self._reactions = reactions
        self._elastic = elastic

    async def search(
        self, user: User, params: CandidateSearchParams, pagination: Pagination
    ) -> CandidateSearchPage:
        vacancy = await self._own_vacancy(user, params.vacancy_id)
        reactions = await self._reactions.for_candidates(user.id)
        query = self._query(params, vacancy, reactions)

        engine, hits = await self._run(query, pagination)
        profiles = await self._candidates.by_ids(hits.ids)
        items = []
        for candidate_id in hits.ids:
            profile = profiles.get(candidate_id)
            if profile is None:  # deleted after indexing
                continue
            facts = CandidateFacts.of(profile)
            result = fit(facts, vacancy, bonus=facts.strength) if vacancy else None
            reaction = reactions.get(candidate_id)
            items.append(
                CandidateMatch(
                    candidate=candidate_read(profile),
                    match_score=result.score if result else None,
                    profile_strength=facts.strength,
                    reasons=candidate_reasons(
                        facts, result, vacancy=vacancy, stack_filter=params.stack
                    ),
                    reaction=reaction.kind if reaction else None,
                )
            )
        return CandidateSearchPage.build(
            items,
            total=hits.total,
            page=pagination.page,
            per_page=pagination.per_page,
            engine=engine,
        )

    async def _own_vacancy(self, user: User, vacancy_id: uuid.UUID | None) -> VacancyFacts | None:
        """Hiring for a vacancy is only possible for the company's own vacancies."""
        if vacancy_id is None:
            return None
        row = await self._vacancies.get(vacancy_id)
        if row is None or row[1].owner_id != user.id:
            raise NotFoundError("Вакансия не найдена")
        return VacancyFacts.of(row[0])

    @staticmethod
    def _query(
        params: CandidateSearchParams,
        vacancy: VacancyFacts | None,
        reactions: dict[uuid.UUID, CandidateReaction],
    ) -> CandidateSearchQuery:
        query = CandidateSearchQuery(
            text=params.text.strip() if params.text and params.text.strip() else None,
            specialization=params.specialization,
            grades=params.grades,
            stack=tuple(item.strip() for item in params.stack if item.strip()),
            has_fsp=params.has_fsp,
            verified_only=params.verified_only,
            work_formats=params.work_formats,
            city=params.city.strip() if params.city and params.city.strip() else None,
            salary_max=params.salary_max,
            experience_min=params.experience_min,
            vacancy=vacancy,
            sort=params.sort,
        )
        if params.view == "liked":
            return replace(query, include_ids=ids_with(reactions, (ReactionKind.LIKE,)))
        # The feed hides skipped candidates; the swipe deck hides everyone already decided on.
        hidden = (ReactionKind.SKIP,) if params.view == "all" else tuple(ReactionKind)
        return replace(query, exclude_ids=ids_with(reactions, hidden))

    async def _run(
        self, query: CandidateSearchQuery, pagination: Pagination
    ) -> tuple[SearchEngine, SearchHits]:
        window = {"offset": pagination.offset, "limit": pagination.per_page}
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
