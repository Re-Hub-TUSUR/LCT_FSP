import uuid
from datetime import datetime

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.enums import EmployerCaseStatus
from app.admin.models import AdminEmployerCase
from app.models import Company, Invitation, InvitationStatus, Vacancy

# The vacancy is named by id alone and may have none (`vacancy_title` is then None): a left join,
# not an inner one.
InvitationRow = tuple[Invitation, Company, str | None]

# Still waiting for the candidate's answer.
OPEN_STATUSES = (InvitationStatus.SENT, InvitationStatus.VIEWED)


class InvitationRepository:
    """Invitations are read together with their company: every card names the employer."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def invite_limit(self, company_id: uuid.UUID) -> int | None:
        """The daily limit an admin set for a restricted company; None when there is none."""
        limit: int | None = await self._session.scalar(
            select(AdminEmployerCase.invite_limit).where(
                AdminEmployerCase.company_id == company_id,
                AdminEmployerCase.status == EmployerCaseStatus.RESTRICTED,
            )
        )
        return limit

    async def sent_since(self, company_id: uuid.UUID, since: datetime) -> int:
        count = await self._session.scalar(
            select(func.count())
            .select_from(Invitation)
            .where(Invitation.company_id == company_id, Invitation.created_at >= since)
        )
        return int(count or 0)

    async def add(self, invitation: Invitation) -> Invitation:
        self._session.add(invitation)
        await self._session.flush()
        await self._session.refresh(invitation)
        return invitation

    async def get(self, invitation_id: uuid.UUID) -> InvitationRow | None:
        row = (
            await self._session.execute(
                select(Invitation, Company, Vacancy.title)
                .join(Company, Company.id == Invitation.company_id)
                .outerjoin(Vacancy, Vacancy.id == Invitation.vacancy_id)
                .where(Invitation.id == invitation_id)
                .with_for_update(of=Invitation)
            )
        ).first()
        return (row[0], row[1], row[2]) if row else None

    async def page_for_candidate(
        self, candidate_id: uuid.UUID, *, limit: int, offset: int
    ) -> tuple[list[InvitationRow], int]:
        return await self._page(Invitation.candidate_id == candidate_id, limit, offset)

    async def page_for_company(
        self, company_id: uuid.UUID, *, limit: int, offset: int
    ) -> tuple[list[InvitationRow], int]:
        return await self._page(Invitation.company_id == company_id, limit, offset)

    async def _page(
        self, condition: ColumnElement[bool], limit: int, offset: int
    ) -> tuple[list[InvitationRow], int]:
        """Newest first."""
        total = await self._session.scalar(
            select(func.count()).select_from(Invitation).where(condition)
        )
        result = await self._session.execute(
            select(Invitation, Company, Vacancy.title)
            .join(Company, Company.id == Invitation.company_id)
            .outerjoin(Vacancy, Vacancy.id == Invitation.vacancy_id)
            .where(condition)
            .order_by(Invitation.created_at.desc(), Invitation.id)
            .limit(limit)
            .offset(offset)
        )
        return [
            (invitation, company, vacancy_title) for invitation, company, vacancy_title in result
        ], total or 0

    async def has_open(self, company_id: uuid.UUID, candidate_id: uuid.UUID) -> bool:
        """Is an invitation of the company still waiting for this candidate's answer?"""
        found = await self._session.scalar(
            select(Invitation.id)
            .where(
                Invitation.company_id == company_id,
                Invitation.candidate_id == candidate_id,
                Invitation.status.in_(OPEN_STATUSES),
            )
            .limit(1)
        )
        return found is not None

    async def accepted_from_owner(self, candidate_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
        """Has the candidate accepted an invitation from the company owned by `owner_id`?"""
        found = await self._session.scalar(
            select(Invitation.id)
            .join(Company, Company.id == Invitation.company_id)
            .where(
                Invitation.candidate_id == candidate_id,
                Invitation.status == InvitationStatus.ACCEPTED,
                Company.owner_id == owner_id,
            )
            .limit(1)
        )
        return found is not None
