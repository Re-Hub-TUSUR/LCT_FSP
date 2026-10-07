"""Likes and skips from the feeds and the swipe decks."""

import uuid

from app.core.errors import NotFoundError
from app.models import CandidateReaction, ReactionKind, User, VacancyReaction
from app.repositories.candidate import CandidateRepository
from app.repositories.company import CompanyRepository
from app.repositories.reaction import ReactionRepository
from app.repositories.vacancy import VacancyRepository
from app.services.notifications import NotificationHub


class ReactionService:
    def __init__(
        self,
        reactions: ReactionRepository,
        vacancies: VacancyRepository,
        candidates: CandidateRepository,
        companies: CompanyRepository | None = None,
        notifications: NotificationHub | None = None,
    ) -> None:
        self._reactions = reactions
        self._vacancies = vacancies
        self._candidates = candidates
        self._companies = companies
        self._notifications = notifications

    async def react_to_vacancy(
        self, user: User, vacancy_id: uuid.UUID, kind: ReactionKind
    ) -> VacancyReaction:
        row = await self._vacancies.get(vacancy_id)
        if row is None or row[0].published_at is None:
            raise NotFoundError("Вакансия не найдена")
        return await self._reactions.set_for_vacancy(user.id, vacancy_id, kind)

    async def clear_vacancy(self, user: User, vacancy_id: uuid.UUID) -> None:
        await self._reactions.clear_for_vacancy(user.id, vacancy_id)

    async def react_to_candidate(
        self,
        user: User,
        candidate_id: uuid.UUID,
        kind: ReactionKind,
        vacancy_id: uuid.UUID | None,
    ) -> CandidateReaction:
        profile = await self._candidates.get(candidate_id)
        if profile is None or not profile.is_visible_to_employers:
            raise NotFoundError("Кандидат не найден")
        if vacancy_id is not None:
            row = await self._vacancies.get(vacancy_id)
            if row is None or row[1].owner_id != user.id:
                raise NotFoundError("Вакансия не найдена")
        reaction = await self._reactions.set_for_candidate(
            user.id, candidate_id, kind, vacancy_id
        )
        if kind == ReactionKind.LIKE and self._notifications and self._companies:
            await self._notify_company_liked(user.id, candidate_id)
        return reaction

    async def _notify_company_liked(
        self, employer_user_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> None:
        if self._notifications is None or self._companies is None:
            return
        company = await self._companies.get_by_owner(employer_user_id)
        profile = await self._candidates.get(candidate_id)
        if company is None or profile is None:
            return
        await self._notifications.publish(
            profile.user_id,
            {
                "type": "company_liked",
                "companyId": str(company.id),
                "companyName": company.name,
            },
        )

    async def clear_candidate(self, user: User, candidate_id: uuid.UUID) -> None:
        await self._reactions.clear_for_candidate(user.id, candidate_id)
