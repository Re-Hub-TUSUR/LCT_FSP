"""The candidate's feed: relevant vacancies only, no free-text search (product decision)."""

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.dependencies.common import Pagination
from app.models import CandidateProfile, ReactionKind, User, VacancyReaction, WorkFormat
from app.repositories.candidate import CandidateRepository
from app.repositories.reaction import ReactionFilter, ReactionRepository
from app.repositories.vacancy import VacancyRepository, VacancyRow
from app.schemas.reaction import FeedView, ReactionCounts
from app.schemas.vacancy import (
    FeedBasis,
    FeedMode,
    VacancyFacets,
    VacancyFeedPage,
    VacancyFeedPresets,
    VacancyFilterSet,
    VacancyMatch,
)
from app.services.matching import (
    CandidateFacts,
    Fit,
    VacancyFacts,
    as_utc,
    fit,
    freshness,
    neighbour_grades,
    related_specializations,
    vacancy_reasons,
)
from app.services.presenters import profile_category, vacancy_read
from app.services.vacancy_filters import (
    ProfileScope,
    VacancyFilterFacts,
    nice_matches,
    passes,
    profile_filters,
    vacancy_facets,
    vacancy_query,
)

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)

Reactions = Mapping[uuid.UUID, VacancyReaction]

# Lists of the user's own decisions: which reaction each of them is built from.
_DECIDED: dict[FeedView, ReactionKind] = {
    "liked": ReactionKind.LIKE,
    "matched": ReactionKind.LIKE,
    "skipped": ReactionKind.SKIP,
}


@dataclass(frozen=True, slots=True)
class VacancyFeedParams:
    mode: FeedMode = "profile"
    filters: VacancyFilterSet = field(default_factory=VacancyFilterSet)
    view: FeedView = "all"


@dataclass(frozen=True, slots=True)
class _Ranked:
    row: VacancyRow
    # None when the feed is not personalised (the candidate has no category yet).
    fit: Fit | None
    # «Будет плюсом» technologies the vacancy asks for.
    nice: int


class VacancyFeedService:
    def __init__(
        self,
        vacancies: VacancyRepository,
        candidates: CandidateRepository,
        reactions: ReactionRepository,
    ) -> None:
        self._vacancies = vacancies
        self._candidates = candidates
        self._reactions = reactions

    async def feed(
        self,
        user: User,
        params: VacancyFeedParams,
        pagination: Pagination,
        *,
        now: datetime | None = None,
    ) -> VacancyFeedPage:
        now = now or datetime.now(UTC)
        profile = await self._candidates.get_by_user(user.id)
        candidate = _personal(profile)
        reactions = await self._reactions.for_vacancies(user.id)
        matched = await self._matched(user, profile)

        query = vacancy_query(params.filters, _scope(candidate, params))
        ranked = []
        for row in await self._rows(user, params.view, matched):
            facts = VacancyFilterFacts.of(*row)
            if passes(facts, query):
                ranked.append(
                    _Ranked(row, self._fit(candidate, row, now), nice_matches(facts, query))
                )
        ordered = self._order(ranked, params.view, reactions, by_fit=query.scope is not None)

        start = pagination.offset
        items = [
            self._match(item, candidate, reactions, matched, now)
            for item in ordered[start : start + pagination.per_page]
        ]
        return VacancyFeedPage.build(
            items,
            total=len(ordered),
            page=pagination.page,
            per_page=pagination.per_page,
            personalized=candidate is not None,
            basis=self._basis(profile),
        )

    async def facets(self, user: User, params: VacancyFeedParams) -> VacancyFacets:
        """Counts next to every filter option of the feed with these parameters."""
        profile = await self._candidates.get_by_user(user.id)
        rows = await self._rows(user, params.view, await self._matched(user, profile))
        return vacancy_facets(
            rows, vacancy_query(params.filters, _scope(_personal(profile), params))
        )

    async def presets(self, user: User, *, view: FeedView = "all") -> VacancyFeedPresets:
        """The feed's modes: matched to the profile, with its filters filled in, or free."""
        profile = await self._candidates.get_by_user(user.id)
        candidate = _personal(profile)
        rows = await self._rows(user, view, await self._matched(user, profile))
        facts = [VacancyFilterFacts.of(*row) for row in rows]
        if profile is None or candidate is None:
            return VacancyFeedPresets(
                personalized=False,
                profile=None,
                profile_count=0,
                category=None,
                free_count=len(facts),
            )
        filters = profile_filters(profile)
        query = vacancy_query(
            filters, _scope(candidate, VacancyFeedParams(filters=filters, view=view))
        )
        return VacancyFeedPresets(
            personalized=True,
            profile=filters,
            profile_count=sum(passes(item, query) for item in facts),
            category=profile_category(profile),
            free_count=len(facts),
        )

    async def counts(self, user: User) -> ReactionCounts:
        """Sizes of the lists `liked`, `matched` and `skipped` as the feed would show them."""
        profile = await self._candidates.get_by_user(user.id)
        matched = await self._matched(user, profile)
        liked = await self._decided(user, ReactionKind.LIKE)
        skipped = await self._decided(user, ReactionKind.SKIP)
        return ReactionCounts(
            liked=len(liked),
            matched=sum(row[0].id in matched for row in liked),
            skipped=len(skipped),
        )

    async def _matched(self, user: User, profile: CandidateProfile | None) -> set[uuid.UUID]:
        # Recruiters like profiles: without one nobody could have liked this account back.
        if profile is None:
            return set()
        return await self._reactions.matched_vacancy_ids(
            candidate_user_id=user.id, candidate_id=profile.id
        )

    async def _decided(self, user: User, kind: ReactionKind) -> list[VacancyRow]:
        """Published vacancies the user reacted to this way, whatever the profile says now."""
        return await self._vacancies.published(
            reactions=ReactionFilter(user.id, (kind,), include=True)
        )

    async def _rows(self, user: User, view: FeedView, matched: set[uuid.UUID]) -> list[VacancyRow]:
        """Published vacancies of the view, before any filter."""
        if view in _DECIDED:
            rows = await self._decided(user, _DECIDED[view])
            return [row for row in rows if row[0].id in matched] if view == "matched" else rows
        # The feed hides skipped cards; the swipe deck hides everything already decided on.
        hidden = (ReactionKind.SKIP,) if view == "all" else tuple(ReactionKind)
        return await self._vacancies.published(
            reactions=ReactionFilter(user.id, hidden, include=False)
        )

    @staticmethod
    def _fit(candidate: CandidateFacts | None, row: VacancyRow, now: datetime) -> Fit | None:
        if candidate is None:
            return None
        vacancy = row[0]
        return fit(candidate, VacancyFacts.of(vacancy), bonus=freshness(vacancy.published_at, now))

    @staticmethod
    def _order(
        ranked: Sequence[_Ranked], view: FeedView, reactions: Reactions, *, by_fit: bool
    ) -> list[_Ranked]:
        if view in _DECIDED:
            # The latest decision first.
            return sorted(
                ranked,
                key=lambda item: (
                    -as_utc(reactions[item.row[0].id].updated_at).timestamp(),
                    str(item.row[0].id),
                ),
            )
        # «Будет плюсом» first, then the best fit to the profile or, in the free search, the newest.
        return sorted(
            ranked,
            key=lambda item: (
                -item.nice,
                -(item.fit.points if by_fit and item.fit else 0.0),
                -as_utc(item.row[0].published_at or _EPOCH).timestamp(),
                str(item.row[0].id),
            ),
        )

    @staticmethod
    def _match(
        item: _Ranked,
        candidate: CandidateFacts | None,
        reactions: Reactions,
        matched: set[uuid.UUID],
        now: datetime,
    ) -> VacancyMatch:
        vacancy, company = item.row
        reaction = reactions.get(vacancy.id)
        reasons = []
        if candidate is not None and item.fit is not None:
            reasons = vacancy_reasons(candidate, VacancyFacts.of(vacancy), item.fit, now=now)
        return VacancyMatch(
            vacancy=vacancy_read(vacancy, company),
            match_score=item.fit.score if item.fit else None,
            reasons=reasons,
            reaction=reaction.kind if reaction else None,
            matched=vacancy.id in matched,
        )

    @staticmethod
    def _basis(profile: CandidateProfile | None) -> FeedBasis | None:
        if profile is None:
            return None
        return FeedBasis(
            category=profile_category(profile),
            grade_verified=profile.assessment_score is not None,
            stack=list(profile.stack),
            work_formats=[WorkFormat(value) for value in profile.work_formats],
            city=profile.city,
            salary_expectation=profile.salary_expectation,
        )


def _personal(profile: CandidateProfile | None) -> CandidateFacts | None:
    """What the feed is personalised by; None until the candidate has a category."""
    if profile is None or profile.specialization is None or profile.grade is None:
        return None
    return CandidateFacts.of(profile)


def _scope(candidate: CandidateFacts | None, params: VacancyFeedParams) -> ProfileScope | None:
    """The profile mode narrows the feed; the lists of own decisions show everything decided."""
    if candidate is None or params.mode != "profile" or params.view in _DECIDED:
        return None
    specialization, grade = candidate.specialization, candidate.grade
    if specialization is None or grade is None:
        return None
    # Priority specialization first in the score; other resumes are included, then ranked lower.
    return ProfileScope(
        specializations=frozenset(
            {specialization, *candidate.other_specializations}
            | related_specializations(specialization)
        ),
        grades=frozenset(item.value for item in (grade, *neighbour_grades(grade))),
    )
