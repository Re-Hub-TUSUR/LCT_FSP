"""Read access to vacancies and companies outside the personalised feed."""

import uuid

from app.core.errors import NotFoundError
from app.dependencies.common import Pagination
from app.models import Grade, User, WorkFormat
from app.repositories.company import CompanyRepository
from app.repositories.vacancy import VacancyRepository
from app.schemas.common import Page
from app.schemas.company import CompanyRead
from app.schemas.vacancy import VacancyRead
from app.services.presenters import company_read, vacancy_read


class VacancyService:
    def __init__(self, vacancies: VacancyRepository, companies: CompanyRepository) -> None:
        self._vacancies = vacancies
        self._companies = companies

    async def public_page(
        self,
        *,
        specialization: str | None,
        grade: Grade | None,
        work_format: WorkFormat | None,
        search: str | None,
        pagination: Pagination,
    ) -> Page[VacancyRead]:
        rows, total = await self._vacancies.page_published(
            specialization=specialization,
            grade=grade,
            work_format=work_format,
            search=search,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        return Page[VacancyRead].build(
            [vacancy_read(vacancy, company) for vacancy, company in rows],
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
        )

    async def read(self, vacancy_id: uuid.UUID, viewer: User | None) -> VacancyRead:
        """A draft exists only for its own company."""
        row = await self._vacancies.get(vacancy_id)
        if row is None:
            raise NotFoundError("Вакансия не найдена")
        vacancy, company = row
        if vacancy.published_at is None and (viewer is None or company.owner_id != viewer.id):
            raise NotFoundError("Вакансия не найдена")
        return vacancy_read(vacancy, company)

    async def mine(self, user: User, pagination: Pagination) -> Page[VacancyRead]:
        company = await self._companies.get_by_owner(user.id)
        rows, total = (
            await self._vacancies.page_for_company(
                company.id, limit=pagination.limit, offset=pagination.offset
            )
            if company is not None
            else ([], 0)
        )
        return Page[VacancyRead].build(
            [vacancy_read(vacancy, owner) for vacancy, owner in rows],
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
        )

    async def company(self, company_id: uuid.UUID) -> CompanyRead:
        company = await self._companies.get(company_id)
        if company is None:
            raise NotFoundError("Компания не найдена")
        return company_read(company)
