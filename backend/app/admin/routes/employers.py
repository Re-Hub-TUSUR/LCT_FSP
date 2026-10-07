import uuid

from fastapi import APIRouter

from app.admin.dependencies import EmployerModerationDep
from app.admin.enums import AnalyticsPeriod
from app.admin.schemas import AnalyticsFilters, EmployerCard, EmployerDecision
from app.dependencies.auth import AdminUser

router = APIRouter(prefix="/employers")


@router.get("/{company_id}", summary="Company card: signals, vacancies, outreach, decisions")
async def employer_card(
    company_id: uuid.UUID,
    _: AdminUser,
    service: EmployerModerationDep,
    period: AnalyticsPeriod = AnalyticsPeriod.QUARTER,
) -> EmployerCard:
    return await service.card(company_id, AnalyticsFilters(period=period))


@router.post(
    "/{company_id}/decision",
    summary="Clear, warn, restrict or block a company (a reason is required)",
    description="«block» also adds the company and its owner's email to the banlist.",
)
async def decide(
    company_id: uuid.UUID, user: AdminUser, data: EmployerDecision, service: EmployerModerationDep
) -> EmployerCard:
    return await service.decide(user, company_id, data)
