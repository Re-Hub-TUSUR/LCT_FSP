"""Inbound likes and responding with mutual interest."""

from app.core.errors import AppError, NotFoundError
from app.models import ReactionKind, User, UserRole
from app.repositories.company import CompanyRepository
from app.repositories.inbound import InboundRepository
from app.schemas.common import SalaryRange
from app.schemas.responses import (
    CandidateInboundRead,
    EmployerInboundRead,
    InboundRespondCandidate,
    InboundRespondEmployer,
)
from app.services.reactions import ReactionService


class ResponsesService:
    def __init__(
        self,
        inbound: InboundRepository,
        reaction_service: ReactionService,
        companies: CompanyRepository,
    ) -> None:
        self._inbound = inbound
        self._reaction_service = reaction_service
        self._companies = companies

    async def inbound_for_user(
        self, user: User
    ) -> list[CandidateInboundRead | EmployerInboundRead]:
        if user.role == UserRole.CANDIDATE:
            companies = await self._inbound.for_candidate(user.id)
            return [
                CandidateInboundRead(
                    company_id=row.company_id,
                    company_name=row.company_name,
                    industry=row.industry,
                    vacancy_id=row.vacancy_id,
                    vacancy_title=row.vacancy_title,
                    salary=(
                        SalaryRange.model_validate({"from": row.salary_from, "to": row.salary_to})
                        if row.salary_from and row.salary_to
                        else None
                    ),
                    reacted_at=row.reacted_at,
                )
                for row in companies
            ]
        if user.role == UserRole.EMPLOYER:
            candidates = await self._inbound.for_employer(user.id)
            return [
                EmployerInboundRead(
                    candidate_id=row.candidate_id,
                    display_name=row.display_name,
                    headline=row.headline,
                    vacancy_id=row.vacancy_id,
                    vacancy_title=row.vacancy_title,
                    reacted_at=row.reacted_at,
                )
                for row in candidates
            ]
        raise AppError("Раздел доступен соискателям и работодателям")

    async def respond_candidate(self, user: User, data: InboundRespondCandidate) -> None:
        company = await self._companies.get(data.company_id)
        if company is None:
            raise NotFoundError("Компания не найдена")
        vacancy_id = data.vacancy_id or await self._inbound.first_published_vacancy(company.id)
        if vacancy_id is None:
            raise NotFoundError("У компании нет опубликованных вакансий")
        await self._reaction_service.react_to_vacancy(user, vacancy_id, ReactionKind.LIKE)

    async def respond_employer(self, user: User, data: InboundRespondEmployer) -> None:
        await self._reaction_service.react_to_candidate(
            user, data.candidate_id, ReactionKind.LIKE, data.vacancy_id
        )
