import uuid
from collections.abc import Collection, Sequence
from datetime import datetime

from sqlalchemy import ColumnElement, Select, exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import CandidateProfile, FspAchievement, Grade, User


class CandidateRepository:
    """Profiles are loaded with their FSP results: every card and every ranking needs them."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _profiles() -> Select[CandidateProfile]:
        return select(CandidateProfile).options(selectinload(CandidateProfile.fsp_achievements))

    async def get(self, candidate_id: uuid.UUID) -> CandidateProfile | None:
        result = await self._session.scalars(
            self._profiles().where(CandidateProfile.id == candidate_id)
        )
        return result.first()

    async def get_by_user(self, user_id: uuid.UUID) -> CandidateProfile | None:
        result = await self._session.scalars(
            self._profiles().where(CandidateProfile.user_id == user_id)
        )
        return result.first()

    async def get_by_fsp_member(self, member_id: str) -> CandidateProfile | None:
        result = await self._session.scalars(
            self._profiles().where(CandidateProfile.fsp_member_id == member_id)
        )
        return result.first()

    async def add(self, profile: CandidateProfile) -> CandidateProfile:
        self._session.add(profile)
        await self._session.flush()
        # A computed column is not set on a new row, and a lazy load is not allowed in async.
        await self._session.refresh(profile, ["last_active_at"])
        return profile

    async def by_ids(self, ids: Collection[uuid.UUID]) -> dict[uuid.UUID, CandidateProfile]:
        if not ids:
            return {}
        result = await self._session.scalars(self._profiles().where(CandidateProfile.id.in_(ids)))
        return {profile.id: profile for profile in result}

    async def all(self) -> Sequence[CandidateProfile]:
        """Every profile, hidden ones included: the search index filters by visibility itself."""
        result = await self._session.scalars(self._profiles().order_by(CandidateProfile.id))
        return result.all()

    async def updated_since(self, moment: datetime) -> Sequence[CandidateProfile]:
        """Profiles changed after `moment`: what the search index has to catch up on."""
        result = await self._session.scalars(
            self._profiles().where(CandidateProfile.updated_at > moment)
        )
        return result.all()

    async def searchable(
        self,
        *,
        specialization: str | None = None,
        grades: Collection[Grade] = (),
        has_fsp: bool | None = None,
        verified_only: bool = False,
        salary_max: int | None = None,
        experience_min: int | None = None,
        include_ids: Collection[uuid.UUID] | None = None,
        exclude_ids: Collection[uuid.UUID] = (),
    ) -> Sequence[CandidateProfile]:
        """Visible, categorised profiles narrowed by the filters a relational query can apply."""
        conditions: list[ColumnElement[bool]] = [
            CandidateProfile.is_visible_to_employers.is_(True),
            CandidateProfile.specialization.is_not(None),
            CandidateProfile.grade.is_not(None),
        ]
        if specialization is not None:
            conditions.append(CandidateProfile.specialization == specialization)
        if grades:
            conditions.append(CandidateProfile.grade.in_(grades))
        if has_fsp is not None:
            with_results = exists().where(FspAchievement.candidate_id == CandidateProfile.id)
            conditions.append(with_results if has_fsp else ~with_results)
        if verified_only:
            conditions.append(CandidateProfile.assessment_score.is_not(None))
        if salary_max is not None:
            conditions.append(
                CandidateProfile.salary_expectation.is_(None)
                | (CandidateProfile.salary_expectation <= salary_max)
            )
        if experience_min is not None:
            conditions.append(CandidateProfile.experience_years >= experience_min)
        if include_ids is not None:
            conditions.append(CandidateProfile.id.in_(include_ids))
        if exclude_ids:
            conditions.append(CandidateProfile.id.not_in(exclude_ids))
        result = await self._session.scalars(self._profiles().where(*conditions))
        return result.all()

    async def email_of(self, profile: CandidateProfile) -> str | None:
        return await self._session.scalar(select(User.email).where(User.id == profile.user_id))

    async def photo_of(self, candidate_id: uuid.UUID) -> tuple[bytes, str] | None:
        """Load the image bytes. The column is deferred on ordinary profile queries."""
        row = (
            await self._session.execute(
                select(CandidateProfile.photo, CandidateProfile.photo_type).where(
                    CandidateProfile.id == candidate_id
                )
            )
        ).one_or_none()
        if row is None or row.photo is None or row.photo_type is None:
            return None
        return row.photo, row.photo_type
