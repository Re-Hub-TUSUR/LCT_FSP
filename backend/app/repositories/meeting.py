import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CandidateProfile, Company, Meeting, MeetingStatus, Vacancy

# A meeting with what its card shows: company name, candidate name, vacancy title.
MeetingRow = tuple[Meeting, str, str, str | None]


class MeetingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, meeting_id: uuid.UUID) -> Meeting | None:
        return await self._session.get(Meeting, meeting_id)

    async def in_range(
        self,
        *,
        starts_before: datetime,
        ends_after: datetime,
        company_id: uuid.UUID | None = None,
        candidate_id: uuid.UUID | None = None,
    ) -> Sequence[MeetingRow]:
        """Meetings of one side that touch the range, earliest first."""
        statement = (
            select(Meeting, Company.name, CandidateProfile.display_name, Vacancy.title)
            .join(Company, Company.id == Meeting.company_id)
            .join(CandidateProfile, CandidateProfile.id == Meeting.candidate_id)
            .outerjoin(Vacancy, Vacancy.id == Meeting.vacancy_id)
            .where(Meeting.starts_at < starts_before, Meeting.ends_at > ends_after)
            .order_by(Meeting.starts_at, Meeting.id)
        )
        if company_id is not None:
            statement = statement.where(Meeting.company_id == company_id)
        if candidate_id is not None:
            statement = statement.where(Meeting.candidate_id == candidate_id)
        result = await self._session.execute(statement)
        return [
            (meeting, company, candidate, vacancy)
            for meeting, company, candidate, vacancy in result
        ]

    async def company_is_busy(
        self,
        company_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
        *,
        except_id: uuid.UUID | None = None,
    ) -> bool:
        """Does the company already hold a meeting (not declined) inside this time?"""
        statement = select(Meeting.id).where(
            Meeting.company_id == company_id,
            Meeting.status != MeetingStatus.DECLINED,
            Meeting.starts_at < ends_at,
            Meeting.ends_at > starts_at,
        )
        if except_id is not None:
            statement = statement.where(Meeting.id != except_id)
        return await self._session.scalar(statement.limit(1)) is not None

    async def add(self, meeting: Meeting) -> Meeting:
        self._session.add(meeting)
        await self._session.flush()
        return meeting

    async def delete(self, meeting: Meeting) -> None:
        await self._session.delete(meeting)
        await self._session.flush()
