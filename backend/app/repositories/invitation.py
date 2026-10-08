import uuid

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company, Invitation, InvitationStatus

InvitationRow = tuple[Invitation, Company]

# Still waiting for the candidate's answer.
OPEN_STATUSES = (InvitationStatus.SENT, InvitationStatus.VIEWED)


class InvitationRepository:
    """Invitations are read together with their company: every card names the employer."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, invitation: Invitation) -> Invitation:
        self._session.add(invitation)
        await self._session.flush()
        await self._session.refresh(invitation)
        return invitation

    async def get(self, invitation_id: uuid.UUID) -> InvitationRow | None:
        row = (
            await self._session.execute(
                select(Invitation, Company)
                .join(Company, Company.id == Invitation.company_id)
                .where(Invitation.id == invitation_id)
                .with_for_update(of=Invitation)
            )
        ).first()
        return (row[0], row[1]) if row else None

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
            select(Invitation, Company)
            .join(Company, Company.id == Invitation.company_id)
            .where(condition)
            .order_by(Invitation.created_at.desc(), Invitation.id)
            .limit(limit)
            .offset(offset)
        )
        return [(invitation, company) for invitation, company in result], total or 0

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
