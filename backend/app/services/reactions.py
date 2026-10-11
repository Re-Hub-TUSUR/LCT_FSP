"""Likes and skips from the feeds and the swipe decks."""

import uuid

from app.admin.activity import KIND_REACTION, ActivityRecorder
from app.core.errors import NotFoundError
from app.models import CandidateReaction, Company, ReactionKind, User, Vacancy, VacancyReaction
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
        *,
        activity: ActivityRecorder | None = None,
    ) -> None:
        self._reactions = reactions
        self._vacancies = vacancies
        self._candidates = candidates
        self._companies = companies
        self._notifications = notifications
        self._activity = activity

    async def react_to_vacancy(
        self, user: User, vacancy_id: uuid.UUID, kind: ReactionKind
    ) -> VacancyReaction:
        row = await self._vacancies.get(vacancy_id)
        if row is None or row[0].published_at is None:
            raise NotFoundError("Вакансия не найдена")
        reaction = await self._reactions.set_for_vacancy(user.id, vacancy_id, kind)
        if kind == ReactionKind.LIKE:
            await self._notify_candidate_applied(user.id, row[0], row[1])
        return reaction

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
        vacancy_title = None
        if vacancy_id is not None:
            row = await self._vacancies.get(vacancy_id)
            if row is None or row[1].owner_id != user.id:
                raise NotFoundError("Вакансия не найдена")
            vacancy_title = row[0].title
        reaction = await self._reactions.set_for_candidate(user.id, candidate_id, kind, vacancy_id)
        await self._note_reaction(user, candidate_id)
        if kind == ReactionKind.LIKE and self._notifications and self._companies:
            await self._notify_company_liked(user.id, candidate_id, vacancy_id, vacancy_title)
        return reaction

    async def _notify_candidate_applied(
        self, candidate_user_id: uuid.UUID, vacancy: Vacancy, company: Company
    ) -> None:
        """The company is already on «Я понравился»: the card has to show up without a reload."""
        if self._notifications is None:
            return
        profile = await self._candidates.get_by_user(candidate_user_id)
        if profile is None:
            return
        # Already mutual: the application belongs on «Взаимно», not on the inbound list.
        prior = (await self._reactions.for_candidates(company.owner_id)).get(profile.id)
        if prior is not None and prior.kind == ReactionKind.LIKE:
            return
        await self._notifications.publish(
            company.owner_id,
            {
                "type": "candidate_applied",
                "candidateId": str(profile.id),
                "displayName": profile.display_name.strip() or "Специалист",
                "vacancyId": str(vacancy.id),
                "vacancyTitle": vacancy.title,
            },
        )

    async def _notify_company_liked(
        self,
        employer_user_id: uuid.UUID,
        candidate_id: uuid.UUID,
        vacancy_id: uuid.UUID | None,
        vacancy_title: str | None,
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
                # The vacancy the recruiter picked the candidate for, if one was named.
                "vacancyId": str(vacancy_id) if vacancy_id else None,
                "vacancyTitle": vacancy_title,
            },
        )

    async def clear_candidate(self, user: User, candidate_id: uuid.UUID) -> None:
        await self._reactions.clear_for_candidate(user.id, candidate_id)
        await self._note_reaction(user, candidate_id)

    async def _note_reaction(self, user: User, candidate_id: uuid.UUID) -> None:
        if self._activity is None or self._companies is None:
            return
        company = await self._companies.get_by_owner(user.id)
        await self._activity.record(KIND_REACTION, user, company, candidate_id)
