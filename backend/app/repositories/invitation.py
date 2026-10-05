import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company, Invitation, InvitationStatus


class InvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
