"""Invitations: a company offers a job to one candidate, the candidate accepts or declines.

An accepted invitation opens the candidate's contacts to that company (`CandidateService`).
"""

import uuid
from datetime import UTC, datetime, timedelta

from app.core.errors import ConflictError, NotFoundError, TooManyRequestsError
from app.dependencies.common import Pagination
from app.models import Company, Invitation, InvitationStatus, User
from app.repositories.candidate import CandidateRepository
from app.repositories.company import CompanyRepository
from app.repositories.invitation import OPEN_STATUSES, InvitationRepository, InvitationRow
from app.repositories.vacancy import VacancyRepository
from app.schemas.common import Page, SalaryRead
from app.schemas.invitation import InvitationCreate, InvitationRead
from app.schemas.vacancy import CompanyRef
from app.services.notifications import NotificationHub


class InvitationService:
    def __init__(
        self,
        invitations: InvitationRepository,
        companies: CompanyRepository,
        candidates: CandidateRepository,
        vacancies: VacancyRepository,
        notifications: NotificationHub,
    ) -> None:
        self._invitations = invitations
        self._companies = companies
        self._candidates = candidates
        self._vacancies = vacancies
        self._notifications = notifications

    async def create(self, user: User, data: InvitationCreate) -> InvitationRead:
        company = await self._companies.get_by_owner(user.id)
        if company is None:
            raise ConflictError("Сначала заполните профиль компании")
        profile = await self._candidates.get(data.candidate_id)
        if profile is None or not profile.is_visible_to_employers:
            raise NotFoundError("Кандидат не найден")
        if data.vacancy_id is not None:
            row = await self._vacancies.get(data.vacancy_id)
            if row is None or row[1].id != company.id:
                raise NotFoundError("Вакансия не найдена")
        if await self._invitations.has_open(company.id, profile.id):
            raise ConflictError("Кандидат ещё не ответил на ваше предыдущее приглашение")
        limit = await self._invitations.invite_limit(company.id)
        if limit is not None:
            since = datetime.now(UTC) - timedelta(days=1)
            if await self._invitations.sent_since(company.id, since) >= limit:
                raise TooManyRequestsError(
                    f"Модератор ограничил компанию: не больше {limit} приглашений в сутки"
                )
        invitation = await self._invitations.add(
            Invitation(
                company_id=company.id,
                candidate_id=profile.id,
                vacancy_id=data.vacancy_id,
                message=data.message.strip(),
                salary_from=data.salary.from_,
                salary_to=data.salary.to,
                contact_method=data.contact_method.strip(),
            )
        )
        await self._notifications.publish(
            profile.user_id,
            {
                "type": "invitation",
                "invitationId": str(invitation.id),
                "companyId": str(company.id),
                "companyName": company.name,
            },
        )
        return _read(invitation, company)

    async def incoming(self, user: User, pagination: Pagination) -> Page[InvitationRead]:
        """A candidate without a resume has no invitations yet: an empty list, not an error."""
        profile = await self._candidates.get_by_user(user.id)
        rows, total = (
            await self._invitations.page_for_candidate(
                profile.id, limit=pagination.limit, offset=pagination.offset
            )
            if profile is not None
            else ([], 0)
        )
        return _page(rows, total, pagination)

    async def outgoing(self, user: User, pagination: Pagination) -> Page[InvitationRead]:
        company = await self._companies.get_by_owner(user.id)
        rows, total = (
            await self._invitations.page_for_company(
                company.id, limit=pagination.limit, offset=pagination.offset
            )
            if company is not None
            else ([], 0)
        )
        return _page(rows, total, pagination)

    async def respond(
        self, user: User, invitation_id: uuid.UUID, *, accept: bool
    ) -> InvitationRead:
        profile = await self._candidates.get_by_user(user.id)
        row = await self._invitations.get(invitation_id)
        if profile is None or row is None or row[0].candidate_id != profile.id:
            raise NotFoundError("Приглашение не найдено")
        invitation, company = row
        if invitation.status not in OPEN_STATUSES:
            raise ConflictError("На это приглашение уже дан ответ")
        invitation.status = InvitationStatus.ACCEPTED if accept else InvitationStatus.DECLINED
        await self._invitations.add(invitation)
        await self._notifications.publish(
            company.owner_id,
            {
                "type": "invitation_answered",
                "invitationId": str(invitation.id),
                "candidateId": str(profile.id),
                "status": invitation.status.value,
            },
        )
        return _read(invitation, company)


def _read(invitation: Invitation, company: Company) -> InvitationRead:
    return InvitationRead(
        id=invitation.id,
        candidate_id=invitation.candidate_id,
        company=CompanyRef(id=company.id, name=company.name),
        vacancy_id=invitation.vacancy_id,
        message=invitation.message,
        salary=SalaryRead.model_validate(
            {"from": invitation.salary_from, "to": invitation.salary_to}
        ),
        contact_method=invitation.contact_method,
        status=invitation.status,
        created_at=invitation.created_at,
        updated_at=invitation.updated_at,
    )


def _page(rows: list[InvitationRow], total: int, pagination: Pagination) -> Page[InvitationRead]:
    return Page[InvitationRead].build(
        [_read(invitation, company) for invitation, company in rows],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
    )
