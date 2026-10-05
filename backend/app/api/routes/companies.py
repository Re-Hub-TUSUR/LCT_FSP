import uuid

from fastapi import APIRouter

from app.api.routes.assessment_bank import bank_router
from app.api.stub import not_implemented
from app.dependencies.auth import EmployerUser
from app.schemas.company import CompanyRead, CompanyUpsert

router = APIRouter(prefix="/companies", tags=["companies"])
# Tasks and tests written by the employer.
router.include_router(bank_router(EmployerUser), prefix="/me")


@router.get("/me", summary="Company profile of the signed-in employer")
async def read_my_company(_: EmployerUser) -> CompanyRead:
    not_implemented("companies.read_me")


@router.put("/me", summary="Create or update the employer's company profile")
async def upsert_my_company(_: EmployerUser, data: CompanyUpsert) -> CompanyRead:
    not_implemented("companies.upsert_me")


@router.get("/{company_id}", summary="Public company page")
async def read_company(company_id: uuid.UUID) -> CompanyRead:
    not_implemented("companies.read")
