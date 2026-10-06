"""The candidate's feed: relevant vacancies only, no free-text search (product decision)."""

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from app.dependencies.common import Pagination
from app.models import CandidateProfile, ReactionKind, User, VacancyReaction, WorkFormat
from app.repositories.candidate import CandidateRepository
from app.repositories.reaction import ReactionFilter, ReactionRepository
from app.repositories.vacancy import VacancyRepository, VacancyRow
from app.schemas.reaction import FeedView, ReactionCounts
from app.schemas.vacancy import FeedBasis, VacancyFeedPage, VacancyMatch
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

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)

Reactions = Mapping[uuid.UUID, VacancyReaction]

# Lists of the user's own decisions: which reaction each of them is built from.
_DECIDED: dict[FeedView, ReactionKind] = {
    "liked": ReactionKind.LIKE,
    "matched": ReactionKind.LIKE,
    "skipped": ReactionKind.SKIP,
}


@dataclass(frozen=True, slots=True)
class VacancyFeedFilters:
    """Light refinements on top of the relevance pre-filter."""

    work_formats: tuple[WorkFormat, ...] = ()
    salary_min: int | None = None


@dataclass(frozen=True, slots=True)
class _Ranked:
    row: VacancyRow
    # None when the feed is not personalised (the candidate has no category yet).
    fit: Fit | None


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
        *,
        view: FeedView,
        filters: VacancyFeedFilters,
        pagination: Pagination,
        now: datetime | None = None,
    ) -> VacancyFeedPage:
        now = now or datetime.now(UTC)
        profile = await self._candidates.get_by_user(user.id)
        candidate = CandidateFacts.of(profile) if profile is not None else None
        if candidate is not None and (candidate.specialization is None or candidate.grade is None):
            candidate = None  # no category yet: nothing to personalise by
        reactions = await self._reactions.for_vacancies(user.id)
        matched = await self._matched(user, profile)

        rows = await self._load(user, candidate, view, filters)
        if view == "matched":
            rows = [row for row in rows if row[0].id in matched]
        ranked = [_Ranked(row, self._fit(candidate, row, now)) for row in rows]
        ordered = self._order(ranked, view, reactions)

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

    async def _decided(
        self, user: User, kind: ReactionKind, filters: VacancyFeedFilters | None = None
    ) -> list[VacancyRow]:
        """Published vacancies the user reacted to this way, whatever the profile says now."""
        filters = filters or VacancyFeedFilters()
        return await self._vacancies.published(
            work_formats=filters.work_formats,
            salary_min=filters.salary_min,
            reactions=ReactionFilter(user.id, (kind,), include=True),
        )

    async def _load(
        self,
        user: User,
        candidate: CandidateFacts | None,
        view: FeedView,
        filters: VacancyFeedFilters,
    ) -> list[VacancyRow]:
        if view in _DECIDED:
            return await self._decided(user, _DECIDED[view], filters)

        # The feed hides skipped cards; the swipe deck hides everything already decided on.
        hidden = (ReactionKind.SKIP,) if view == "all" else tuple(ReactionKind)
        exclude = ReactionFilter(user.id, hidden, include=False)
        if candidate is None or candidate.specialization is None or candidate.grade is None:
            return await self._vacancies.published(
                work_formats=filters.work_formats, salary_min=filters.salary_min, reactions=exclude
            )

        # Priority specialization first in the score; other resumes are included, then ranked lower.
        return await self._vacancies.published(
            specializations={candidate.specialization}
            | set(candidate.other_specializations)
            | related_specializations(candidate.specialization),
            grades={candidate.grade, *neighbour_grades(candidate.grade)},
            work_formats=filters.work_formats,
            salary_min=filters.salary_min,
            reactions=exclude,
        )

    @staticmethod
    def _fit(candidate: CandidateFacts | None, row: VacancyRow, now: datetime) -> Fit | None:
        if candidate is None:
            return None
        vacancy = row[0]
        return fit(candidate, VacancyFacts.of(vacancy), bonus=freshness(vacancy.published_at, now))

    @staticmethod
    def _order(ranked: Sequence[_Ranked], view: FeedView, reactions: Reactions) -> list[_Ranked]:
        if view in _DECIDED:
            # The latest decision first.
            return sorted(
                ranked,
                key=lambda item: (
                    -as_utc(reactions[item.row[0].id].updated_at).timestamp(),
                    str(item.row[0].id),
                ),
            )
        # Best fit first; without a profile simply the newest.
        return sorted(
            ranked,
            key=lambda item: (
                -(item.fit.points if item.fit else 0.0),
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
