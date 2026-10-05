import uuid
from collections.abc import Collection
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CandidateReaction, ReactionKind, VacancyReaction


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
