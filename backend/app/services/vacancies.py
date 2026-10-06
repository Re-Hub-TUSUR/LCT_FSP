"""Read access to vacancies and companies outside the personalised feed."""

import uuid

from app.core.errors import NotFoundError
from app.dependencies.common import Pagination
from app.models import Company, Grade, User, WorkFormat
from app.repositories.company import CompanyRepository
from app.repositories.vacancy import VacancyRepository
from app.schemas.common import Page
from app.schemas.company import CompanyRead, CompanyUpsert
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

    async def read_mine(self, user: User) -> CompanyRead:
        company = await self._companies.get_by_owner(user.id)
        if company is None:
            raise NotFoundError("Профиль компании ещё не заполнен")
        return company_read(company)

    async def upsert_mine(self, user: User, data: CompanyUpsert) -> CompanyRead:
        company = await self._companies.get_by_owner(user.id)
        website = str(data.website)
        contact = str(data.contact_email)
        size = data.size.strip() if data.size else None
        if company is None:
            company = Company(
                owner_id=user.id,
                name=data.name.strip(),
                industry=data.industry.strip(),
                description=data.description.strip(),
                city=data.city.strip(),
                size=size or None,
                website=website,
                contact_email=contact,
            )
            await self._companies.add(company)
        else:
            company.name = data.name.strip()
            company.industry = data.industry.strip()
            company.description = data.description.strip()
            company.city = data.city.strip()
            company.size = size or None
            company.website = website
            company.contact_email = contact
        return company_read(company)
