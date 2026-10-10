import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.enums import VerificationStatus
from app.admin.models import CompanyVerification
from app.models import Company


class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, company_id: uuid.UUID) -> Company | None:
        return await self._session.get(Company, company_id)

    async def get_by_owner(self, user_id: uuid.UUID) -> Company | None:
        return await self._session.scalar(select(Company).where(Company.owner_id == user_id))

    async def add(self, company: Company) -> Company:
        self._session.add(company)
        await self._session.flush()
        # A computed column is not set on a new row, and a lazy load is not allowed in async.
        await self._session.refresh(company, ["it_accredited"])
        return company

    async def reopen_verification(self, company: Company, reason: str) -> None:
        """An approved check goes back to the admins; the mark is off until they decide."""
        await self._session.execute(
            update(CompanyVerification)
            .where(
                CompanyVerification.company_id == company.id,
                CompanyVerification.status == VerificationStatus.APPROVED,
            )
            .values(
                status=VerificationStatus.PENDING,
                decided_at=None,
                decided_by=None,
                decision_reason=reason,
            )
            .execution_options(synchronize_session=False)
        )
        await self._session.flush()
        await self._session.refresh(company, ["it_accredited"])

    async def logo_of(self, company_id: uuid.UUID) -> tuple[bytes, str] | None:
        row = (
            await self._session.execute(
                select(Company.logo, Company.logo_type).where(Company.id == company_id)
            )
        ).first()
        if row is None or row.logo is None or row.logo_type is None:
            return None
        return row.logo, row.logo_type

    async def inn_taken(self, inn: str, *, except_id: uuid.UUID | None) -> bool:
        query = select(Company.id).where(Company.inn == inn)
        if except_id is not None:
            query = query.where(Company.id != except_id)
        return await self._session.scalar(query.limit(1)) is not None
