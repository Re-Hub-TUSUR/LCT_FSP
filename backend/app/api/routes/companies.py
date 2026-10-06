import uuid

from fastapi import APIRouter

from app.api.routes.assessment_bank import bank_router
from app.dependencies.auth import EmployerUser
from app.dependencies.services import VacancyServiceDep
from app.schemas.company import CompanyRead, CompanyUpsert

router = APIRouter(prefix="/companies", tags=["companies"])
# Tasks and tests written by the employer.
router.include_router(bank_router(EmployerUser), prefix="/me")


@router.get("/me", summary="Company profile of the signed-in employer")
async def read_my_company(user: EmployerUser, vacancies: VacancyServiceDep) -> CompanyRead:
    return await vacancies.read_mine(user)


@router.put("/me", summary="Create or update the employer's company profile")
async def upsert_my_company(
    user: EmployerUser, data: CompanyUpsert, vacancies: VacancyServiceDep
) -> CompanyRead:
    return await vacancies.upsert_mine(user, data)


@router.get("/{company_id}", summary="Public company page")
async def read_company(company_id: uuid.UUID, vacancies: VacancyServiceDep) -> CompanyRead:
    return await vacancies.company(company_id)
