import uuid

from fastapi import APIRouter, Response, UploadFile

from app.api.routes.assessment_bank import bank_router
from app.dependencies.auth import EmployerUser
from app.dependencies.services import VacancyServiceDep
from app.schemas.company import CompanyRead, CompanyUpsert
from app.services.uploads import PHOTO_LIMIT

router = APIRouter(prefix="/companies", tags=["companies"])
# Tasks and tests written by the employer.
router.include_router(bank_router(EmployerUser), prefix="/me")


@router.get(
    "/me",
    summary="Company profile of the signed-in employer",
    description="`null` until the profile is filled in.",
)
async def read_my_company(user: EmployerUser, vacancies: VacancyServiceDep) -> CompanyRead | None:
    return await vacancies.read_mine(user)


@router.put(
    "/me",
    summary="Create or update the employer's company profile",
    description="The INN is checked by its check digits; a second company with it answers 409.",
)
async def upsert_my_company(
    user: EmployerUser, data: CompanyUpsert, vacancies: VacancyServiceDep
) -> CompanyRead:
    return await vacancies.upsert_mine(user, data)


@router.post("/me/logo", summary="Upload the company logo (JPEG, PNG or WebP, up to 2 MB)")
async def upload_logo(
    user: EmployerUser, file: UploadFile, vacancies: VacancyServiceDep
) -> CompanyRead:
    return await vacancies.set_logo(user, await file.read(PHOTO_LIMIT + 1))


@router.delete("/me/logo", summary="Remove the company logo")
async def delete_logo(user: EmployerUser, vacancies: VacancyServiceDep) -> CompanyRead:
    return await vacancies.clear_logo(user)


@router.get("/{company_id}/logo", summary="Company logo, public like the company page")
async def read_logo(company_id: uuid.UUID, vacancies: VacancyServiceDep) -> Response:
    body, media = await vacancies.open_logo(company_id)
    return Response(
        content=body,
        media_type=media,
        headers={
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": "inline",
            "Cache-Control": "public, max-age=300",
        },
    )


@router.get("/{company_id}", summary="Public company page")
async def read_company(company_id: uuid.UUID, vacancies: VacancyServiceDep) -> CompanyRead:
    return await vacancies.company(company_id)
