import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import exists, select
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
class CandidateInboundRow:
    company_id: uuid.UUID
    company_name: str
    industry: str | None
    recruiter_id: uuid.UUID
    vacancy_id: uuid.UUID | None
    reacted_at: datetime


@dataclass(frozen=True, slots=True)
class EmployerInboundRow:
    candidate_id: uuid.UUID
    display_name: str
    headline: str | None
    vacancy_id: uuid.UUID
    vacancy_title: str
    reacted_at: datetime


class InboundRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def for_candidate(self, candidate_user_id: uuid.UUID) -> list[CandidateInboundRow]:
        profile = await self._session.scalar(
            select(CandidateProfile).where(CandidateProfile.user_id == candidate_user_id)
        )
        if profile is None:
            return []

        liked_back = exists().where(
            VacancyReaction.user_id == candidate_user_id,
            VacancyReaction.kind == ReactionKind.LIKE,
            VacancyReaction.vacancy_id == Vacancy.id,
            Vacancy.company_id == Company.id,
        )
        rows = await self._session.execute(
            select(
                Company.id,
                Company.name,
                Company.industry,
                CandidateReaction.user_id,
                CandidateReaction.vacancy_id,
                CandidateReaction.updated_at,
            )
            .join(Company, Company.owner_id == CandidateReaction.user_id)
            .where(
                CandidateReaction.candidate_id == profile.id,
                CandidateReaction.kind == ReactionKind.LIKE,
                ~liked_back,
            )
            .order_by(CandidateReaction.updated_at.desc())
        )
        return [
            CandidateInboundRow(
                company_id=company_id,
                company_name=name,
                industry=industry,
                recruiter_id=recruiter_id,
                vacancy_id=vacancy_id,
                reacted_at=reacted_at,
            )
            for company_id, name, industry, recruiter_id, vacancy_id, reacted_at in rows
        ]

    async def for_employer(self, employer_user_id: uuid.UUID) -> list[EmployerInboundRow]:
        company = await self._session.scalar(
            select(Company).where(Company.owner_id == employer_user_id)
        )
        if company is None:
            return []

        recruiter_liked = exists().where(
            CandidateReaction.user_id == employer_user_id,
            CandidateReaction.candidate_id == CandidateProfile.id,
            CandidateReaction.kind == ReactionKind.LIKE,
        )
        rows = await self._session.execute(
            select(
                CandidateProfile.id,
                CandidateProfile.display_name,
                CandidateProfile.headline,
                Vacancy.id,
                Vacancy.title,
                VacancyReaction.updated_at,
            )
            .join(CandidateProfile, CandidateProfile.user_id == VacancyReaction.user_id)
            .join(Vacancy, Vacancy.id == VacancyReaction.vacancy_id)
            .where(
                Vacancy.company_id == company.id,
                VacancyReaction.kind == ReactionKind.LIKE,
                ~recruiter_liked,
            )
            .order_by(VacancyReaction.updated_at.desc())
        )
        seen: set[uuid.UUID] = set()
        result: list[EmployerInboundRow] = []
        for candidate_id, name, headline, vacancy_id, vacancy_title, reacted_at in rows:
            if candidate_id in seen:
                continue
            seen.add(candidate_id)
            result.append(
                EmployerInboundRow(
                    candidate_id=candidate_id,
                    display_name=name,
                    headline=headline,
                    vacancy_id=vacancy_id,
                    vacancy_title=vacancy_title,
                    reacted_at=reacted_at,
                )
            )
        return result

    async def first_published_vacancy(self, company_id: uuid.UUID) -> uuid.UUID | None:
        return await self._session.scalar(
            select(Vacancy.id)
            .where(Vacancy.company_id == company_id, Vacancy.published_at.is_not(None))
            .order_by(Vacancy.published_at.desc())
            .limit(1)
        )
