import uuid
from collections.abc import Collection

from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company, Grade, Vacancy, VacancyReaction, WorkFormat
from app.repositories.reaction import ReactionFilter

VacancyRow = tuple[Vacancy, Company]


class VacancyRepository:
    """Vacancies are always read together with their company: every card shows the employer."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _rows() -> Select[Vacancy, Company]:
        return select(Vacancy, Company).join(Company, Company.id == Vacancy.company_id)

    async def _fetch(self, statement: Select[Vacancy, Company]) -> list[VacancyRow]:
        result = await self._session.execute(statement)
        return [(vacancy, company) for vacancy, company in result]

    async def get(self, vacancy_id: uuid.UUID) -> VacancyRow | None:
        rows = await self._fetch(self._rows().where(Vacancy.id == vacancy_id))
        return rows[0] if rows else None

    async def add(self, vacancy: Vacancy) -> Vacancy:
        self._session.add(vacancy)
        await self._session.flush()
        return vacancy

    async def published(self, *, reactions: ReactionFilter | None = None) -> list[VacancyRow]:
        """Every published vacancy, unordered: the feed filters and ranks them in Python."""
        conditions: list[ColumnElement[bool]] = [Vacancy.published_at.is_not(None)]
        if reactions is not None:
            reacted = select(VacancyReaction.vacancy_id).where(
                VacancyReaction.user_id == reactions.user_id,
                VacancyReaction.kind.in_(reactions.kinds),
            )
            in_reacted = Vacancy.id.in_(reacted)
            conditions.append(in_reacted if reactions.include else ~in_reacted)
        return await self._fetch(self._rows().where(*conditions))

    async def page_published(
        self,
        *,
        specialization: str | None,
        grade: Grade | None,
        work_format: WorkFormat | None,
        search: str | None,
        limit: int,
        offset: int,
        company_id: uuid.UUID | None = None,
    ) -> tuple[list[VacancyRow], int]:
        """The public list, newest first; of one company when `company_id` is given."""
        conditions = self._published_conditions(
            specializations=[specialization] if specialization else None,
            grades=[grade] if grade else None,
            work_formats=[work_format] if work_format else (),
        )
        if company_id is not None:
            conditions.append(Vacancy.company_id == company_id)
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(Vacancy.title.ilike(pattern) | Company.name.ilike(pattern))
        total = await self._session.scalar(
            select(func.count())
            .select_from(Vacancy)
            .join(Company, Company.id == Vacancy.company_id)
            .where(*conditions)
        )
        rows = await self._fetch(
            self._rows()
            .where(*conditions)
            .order_by(Vacancy.published_at.desc(), Vacancy.id)
            .limit(limit)
            .offset(offset)
        )
        return rows, total or 0

    async def for_company(self, company_id: uuid.UUID) -> list[VacancyRow]:
        """All of a company's vacancies: published ones newest first, then drafts."""
        return await self._fetch(
            self._rows()
            .where(Vacancy.company_id == company_id)
            .order_by(
                Vacancy.published_at.desc().nulls_last(), Vacancy.created_at.desc(), Vacancy.id
            )
        )

    async def page_for_company(
        self, company_id: uuid.UUID, *, limit: int, offset: int
    ) -> tuple[list[VacancyRow], int]:
        """A company's own vacancies, drafts first, then the newest."""
        condition = Vacancy.company_id == company_id
        total = await self._session.scalar(
            select(func.count()).select_from(Vacancy).where(condition)
        )
        rows = await self._fetch(
            self._rows()
            .where(condition)
            .order_by(Vacancy.published_at.desc().nulls_first(), Vacancy.id)
            .limit(limit)
            .offset(offset)
        )
        return rows, total or 0

    @staticmethod
    def _published_conditions(
        *,
        specializations: Collection[str] | None,
        grades: Collection[Grade] | None,
        work_formats: Collection[WorkFormat],
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = [Vacancy.published_at.is_not(None)]
        if specializations is not None:
            conditions.append(Vacancy.specialization.in_(specializations))
        if grades is not None:
            conditions.append(Vacancy.grade.in_(grades))
        if work_formats:
            conditions.append(Vacancy.work_format.in_(work_formats))
        return conditions
