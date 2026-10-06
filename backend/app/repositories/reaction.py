import uuid
from collections.abc import Collection
from dataclasses import dataclass

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CandidateProfile,
    CandidateReaction,
    Company,
    ReactionKind,
    Vacancy,
    VacancyReaction,
)


@dataclass(frozen=True, slots=True)
class ReactionFilter:
    """Keep only the cards a user reacted to with `kinds` (`include`), or drop them."""

    user_id: uuid.UUID
    kinds: tuple[ReactionKind, ...]
    include: bool


class ReactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def for_vacancies(self, user_id: uuid.UUID) -> dict[uuid.UUID, VacancyReaction]:
        result = await self._session.scalars(
            select(VacancyReaction).where(VacancyReaction.user_id == user_id)
        )
        return {reaction.vacancy_id: reaction for reaction in result}

    async def for_candidates(self, user_id: uuid.UUID) -> dict[uuid.UUID, CandidateReaction]:
        result = await self._session.scalars(
            select(CandidateReaction).where(CandidateReaction.user_id == user_id)
        )
        return {reaction.candidate_id: reaction for reaction in result}

    async def is_match(
        self,
        *,
        recruiter_id: uuid.UUID,
        company_id: uuid.UUID,
        candidate_id: uuid.UUID,
        candidate_user_id: uuid.UUID,
    ) -> bool:
        """Mutual interest: the recruiter liked the candidate and the candidate liked at least
        one vacancy of the recruiter's company."""
        liked_by_recruiter = await self._session.scalar(
            select(CandidateReaction.id)
            .where(
                CandidateReaction.user_id == recruiter_id,
                CandidateReaction.candidate_id == candidate_id,
                CandidateReaction.kind == ReactionKind.LIKE,
            )
            .limit(1)
        )
        if liked_by_recruiter is None:
            return False
        liked_by_candidate = await self._session.scalar(
            select(VacancyReaction.id)
            .join(Vacancy, Vacancy.id == VacancyReaction.vacancy_id)
            .where(
                VacancyReaction.user_id == candidate_user_id,
                VacancyReaction.kind == ReactionKind.LIKE,
                Vacancy.company_id == company_id,
            )
            .limit(1)
        )
        return liked_by_candidate is not None

    async def matched_vacancy_ids(
        self, *, candidate_user_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> set[uuid.UUID]:
        """Vacancies the candidate liked whose company's recruiter liked the candidate."""
        result = await self._session.scalars(
            select(VacancyReaction.vacancy_id)
            .join(Vacancy, Vacancy.id == VacancyReaction.vacancy_id)
            .join(Company, Company.id == Vacancy.company_id)
            .join(CandidateReaction, CandidateReaction.user_id == Company.owner_id)
            .where(
                VacancyReaction.user_id == candidate_user_id,
                VacancyReaction.kind == ReactionKind.LIKE,
                CandidateReaction.candidate_id == candidate_id,
                CandidateReaction.kind == ReactionKind.LIKE,
            )
        )
        return set(result)

    async def matched_candidate_ids(
        self, *, recruiter_id: uuid.UUID, company_id: uuid.UUID
    ) -> set[uuid.UUID]:
        """Candidates the recruiter liked who liked at least one vacancy of the company."""
        liked_back = exists().where(
            VacancyReaction.user_id == CandidateProfile.user_id,
            VacancyReaction.kind == ReactionKind.LIKE,
            VacancyReaction.vacancy_id == Vacancy.id,
            Vacancy.company_id == company_id,
        )
        result = await self._session.scalars(
            select(CandidateReaction.candidate_id)
            .join(CandidateProfile, CandidateProfile.id == CandidateReaction.candidate_id)
            .where(
                CandidateReaction.user_id == recruiter_id,
                CandidateReaction.kind == ReactionKind.LIKE,
                liked_back,
            )
        )
        return set(result)

    async def set_for_vacancy(
        self, user_id: uuid.UUID, vacancy_id: uuid.UUID, kind: ReactionKind
    ) -> VacancyReaction:
        reaction = await self._session.scalar(
            select(VacancyReaction).where(
                VacancyReaction.user_id == user_id, VacancyReaction.vacancy_id == vacancy_id
            )
        )
        if reaction is None:
            reaction = VacancyReaction(user_id=user_id, vacancy_id=vacancy_id, kind=kind)
            self._session.add(reaction)
        else:
            reaction.kind = kind
        await self._session.flush()
        await self._session.refresh(reaction)
        return reaction

    async def set_for_candidate(
        self,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
        kind: ReactionKind,
        vacancy_id: uuid.UUID | None,
    ) -> CandidateReaction:
        reaction = await self._session.scalar(
            select(CandidateReaction).where(
                CandidateReaction.user_id == user_id,
                CandidateReaction.candidate_id == candidate_id,
            )
        )
        if reaction is None:
            reaction = CandidateReaction(
                user_id=user_id, candidate_id=candidate_id, kind=kind, vacancy_id=vacancy_id
            )
            self._session.add(reaction)
        else:
            reaction.kind = kind
            reaction.vacancy_id = vacancy_id
        await self._session.flush()
        await self._session.refresh(reaction)
        return reaction

    async def clear_for_vacancy(self, user_id: uuid.UUID, vacancy_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(VacancyReaction).where(
                VacancyReaction.user_id == user_id, VacancyReaction.vacancy_id == vacancy_id
            )
        )

    async def clear_for_candidate(self, user_id: uuid.UUID, candidate_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(CandidateReaction).where(
                CandidateReaction.user_id == user_id,
                CandidateReaction.candidate_id == candidate_id,
            )
        )


def ids_with(
    reactions: dict[uuid.UUID, VacancyReaction] | dict[uuid.UUID, CandidateReaction],
    kinds: Collection[ReactionKind],
) -> tuple[uuid.UUID, ...]:
    return tuple(target for target, reaction in reactions.items() if reaction.kind in kinds)
