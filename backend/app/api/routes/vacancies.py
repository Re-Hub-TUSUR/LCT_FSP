import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.stub import not_implemented
from app.dependencies.auth import EmployerUser
from app.dependencies.common import PaginationDep
from app.models.enums import Grade, WorkFormat
from app.schemas.common import Page
from app.schemas.vacancy import VacancyCreate, VacancyRead

router = APIRouter(prefix="/vacancies", tags=["vacancies"])


@router.get("", summary="Published vacancies (public table)")
async def list_vacancies(
    pagination: PaginationDep,
    search: str | None = None,
    specialization: str | None = None,
    grade: Grade | None = None,
    work_format: Annotated[WorkFormat | None, Query(alias="workFormat")] = None,
) -> Page[VacancyRead]:
    not_implemented("vacancies.list")


@router.post("", status_code=status.HTTP_201_CREATED, summary="Publish a vacancy")
async def create_vacancy(_: EmployerUser, data: VacancyCreate) -> VacancyRead:
    not_implemented("vacancies.create")


@router.get("/{vacancy_id}", summary="Vacancy details")
async def read_vacancy(vacancy_id: uuid.UUID) -> VacancyRead:
    not_implemented("vacancies.read")


@router.patch("/{vacancy_id}", summary="Edit own vacancy")
async def update_vacancy(
    vacancy_id: uuid.UUID, _: EmployerUser, data: VacancyCreate
) -> VacancyRead:
    not_implemented("vacancies.update")
