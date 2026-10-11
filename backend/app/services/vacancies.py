"""Vacancies and companies outside the personalised feed: public reads and the employer's own."""

import uuid
from datetime import UTC, datetime
from typing import Any

from app.admin.activity import KIND_INDUSTRY, KIND_JUNK, KIND_REQUISITES, ActivityRecorder
from app.admin.dictionaries import INDUSTRY_VALUES
from app.core.errors import AppError, ConflictError, NotFoundError
from app.dependencies.common import Pagination
from app.models import Company, Grade, User, Vacancy, WorkFormat
from app.repositories.company import CompanyRepository
from app.repositories.vacancy import VacancyRepository
from app.schemas.common import Page
from app.schemas.company import CompanyRead, CompanyUpsert
from app.schemas.vacancy import (
    MIN_DESCRIPTION_WORDS,
    VacancyCreate,
    VacancyRead,
    _has_word,
    _words,
)
from app.services.categories import SPECIALIZATIONS
from app.services.cities import CityDirectory, place_fields
from app.services.inn import ORGANISATION_LENGTH as ORGANISATION_INN_LENGTH
from app.services.presenters import company_read, vacancy_read
from app.services.uploads import PHOTO_LIMIT, sniff_image

# Details the accreditation was checked against: changing any of them reopens the check.
CHECKED_FIELDS = ("name", "inn", "ogrn", "kpp", "legal_address")
# One event when any of these differ from the stored company.
REQUISITE_FIELDS = ("name", "inn", "kpp", "ogrn", "industry")


class VacancyService:
    def __init__(
        self,
        vacancies: VacancyRepository,
        companies: CompanyRepository,
        cities: CityDirectory,
        activity: ActivityRecorder | None = None,
    ) -> None:
        self._vacancies = vacancies
        self._companies = companies
        self._cities = cities
        self._activity = activity

    async def public_page(
        self,
        *,
        specialization: str | None,
        grade: Grade | None,
        work_format: WorkFormat | None,
        search: str | None,
        pagination: Pagination,
        company_id: uuid.UUID | None = None,
    ) -> Page[VacancyRead]:
        rows, total = await self._vacancies.page_published(
            company_id=company_id,
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

    async def create(self, user: User, data: VacancyCreate) -> VacancyRead:
        company = await self._require_mine(user)
        await self._require_words(user, company, data)
        vacancy = Vacancy(company_id=company.id, **_columns(data, await _place(self._cities, data)))
        vacancy.published_at = datetime.now(UTC) if data.publish else None
        await self._vacancies.add(vacancy)
        return vacancy_read(vacancy, company)

    async def update(self, user: User, vacancy_id: uuid.UUID, data: VacancyCreate) -> VacancyRead:
        row = await self._vacancies.get(vacancy_id)
        if row is None or row[1].owner_id != user.id:
            raise NotFoundError("Вакансия не найдена")
        vacancy, company = row
        await self._require_words(user, company, data)
        for name, value in _columns(data, await _place(self._cities, data)).items():
            setattr(vacancy, name, value)
        # The date of the first publication survives later edits.
        if not data.publish:
            vacancy.published_at = None
        elif vacancy.published_at is None:
            vacancy.published_at = datetime.now(UTC)
        return vacancy_read(vacancy, company)

    async def company(self, company_id: uuid.UUID) -> CompanyRead:
        company = await self._companies.get(company_id)
        if company is None:
            raise NotFoundError("Компания не найдена")
        return company_read(company)

    async def read_mine(self, user: User) -> CompanyRead | None:
        """None until the employer fills the company profile in: that is not an error."""
        company = await self._companies.get_by_owner(user.id)
        return company_read(company) if company else None

    async def upsert_mine(self, user: User, data: CompanyUpsert) -> CompanyRead:
        company = await self._companies.get_by_owner(user.id)
        industry = data.industry.strip()
        if industry not in INDUSTRY_VALUES:
            await self._reject(user, company, KIND_INDUSTRY, "Выберите направление из списка")
        if await self._companies.inn_taken(data.inn, except_id=company.id if company else None):
            raise ConflictError("Компания с таким ИНН уже зарегистрирована")
        address = data.legal_address.strip() if data.legal_address else None
        fields = {
            "name": data.name.strip(),
            "industry": industry,
            "description": data.description.strip(),
            "city": data.city.strip(),
            "size": data.size,
            "website": str(data.website),
            "contact_email": str(data.contact_email),
            "inn": data.inn,
            "ogrn": data.ogrn,
            # A sole trader (12-digit INN) has no KPP.
            "kpp": data.kpp if len(data.inn) == ORGANISATION_INN_LENGTH else None,
            "legal_address": address or None,
        }
        requisites_changed = company is not None and any(
            getattr(company, name) != fields[name] for name in REQUISITE_FIELDS
        )
        if company is None:
            company = await self._companies.add(Company(owner_id=user.id, **fields))
        else:
            changed = any(getattr(company, name) != fields[name] for name in CHECKED_FIELDS)
            for name, value in fields.items():
                setattr(company, name, value)
            if changed and company.it_accredited:
                # The accreditation was checked for the old details: another company could
                # otherwise borrow the mark by retyping its own.
                await self._companies.reopen_verification(
                    company, "Реквизиты компании изменились: нужна повторная проверка"
                )
        if requisites_changed and self._activity is not None:
            await self._activity.record(KIND_REQUISITES, user, company)
            # The flush expires the accreditation mark; reading it afterwards is not async.
            await self._companies._session.refresh(company, ["it_accredited"])
        return company_read(company)

    async def _require_words(self, user: User, company: Company, data: VacancyCreate) -> None:
        """A digit-only offer is rejected and counted. A thin one is rejected the same way."""
        if not _has_letters(data.title) or not _has_letters(data.description):
            message = "Опишите вакансию словами"
        elif not _has_word(data.title):
            message = "Название вакансии — словами, например «Backend-разработчик»"
        elif _words(data.description) < MIN_DESCRIPTION_WORDS:
            message = "Опишите вакансию словами: задачи, команда, условия"
        else:
            return
        await self._reject(user, company, KIND_JUNK, message)

    async def _reject(
        self, user: User, company: Company | None, kind: str, message: str
    ) -> None:
        """Keep the rejected attempt. The error rolls the rest of the request back."""
        if self._activity is not None and company is not None:
            await self._activity.record(kind, user, company)
            await self._companies._session.commit()
        raise AppError(message)

    async def set_logo(self, user: User, data: bytes) -> CompanyRead:
        company = await self._require_mine(user)
        if len(data) > PHOTO_LIMIT:
            raise AppError("Логотип больше 2 МБ")
        media = sniff_image(data)
        if media is None:
            raise AppError("Нужен логотип JPEG, PNG или WebP")
        company.logo = data
        company.logo_type = media
        return company_read(company)

    async def clear_logo(self, user: User) -> CompanyRead:
        company = await self._require_mine(user)
        company.logo = None
        company.logo_type = None
        return company_read(company)

    async def open_logo(self, company_id: uuid.UUID) -> tuple[bytes, str]:
        logo = await self._companies.logo_of(company_id)
        if logo is None:
            raise NotFoundError("Логотип не загружен")
        return logo

    async def _require_mine(self, user: User) -> Company:
        company = await self._companies.get_by_owner(user.id)
        if company is None:
            raise NotFoundError("Сначала заполните и сохраните профиль компании")
        return company


def _has_letters(value: str) -> bool:
    return any(character.isalpha() for character in value)


async def _place(cities: CityDirectory, data: VacancyCreate):
    """Remote work has no office. Otherwise the place comes from the dictionary."""
    if data.work_format == WorkFormat.REMOTE:
        return None
    return await cities.require(data.city_id, data.city)


def _columns(data: VacancyCreate, city) -> dict[str, Any]:
    """The recruiter's form as the columns of `Vacancy`, publication aside."""
    if data.specialization not in SPECIALIZATIONS:
        raise AppError("Неизвестная специализация")
    grades = sorted(set(data.grades), key=list(Grade).index)
    remote = data.work_format == WorkFormat.REMOTE
    return {
        "title": data.title.strip(),
        "description": data.description.strip(),
        "specialization": data.specialization,
        "grade": grades[0],
        "grades": [grade.value for grade in grades],
        "stack": [*data.stack_required, *data.stack_nice],
        "stack_required": data.stack_required,
        "stack_nice": data.stack_nice,
        "salary_from": data.salary.from_,
        "salary_to": data.salary.to,
        "work_format": data.work_format,
        **place_fields(None if remote else city),
        "relocation_help": data.relocation_help,
        "employment_types": [item.value for item in dict.fromkeys(data.employment_types)],
        "benefits": [item.value for item in dict.fromkeys(data.benefits)],
        "verified_grade_only": data.verified_grade_only,
        "fsp_best_result": data.fsp_best_result,
        "fsp_discipline": data.fsp_discipline,
        "min_experience_years": data.min_experience_years,
    }
