import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CandidateUser, CurrentUser, EmployerUser
from app.dependencies.services import ResponsesServiceDep
from app.schemas.responses import (
    CandidateInboundRead,
    EmployerInboundRead,
    InboundRespondCandidate,
    InboundRespondEmployer,
)

router = APIRouter(prefix="/responses", tags=["responses"])


@router.get(
    "/inbound",
    summary="Incoming likes without mutual interest yet",
)
async def list_inbound(
    user: CurrentUser,
    service: ResponsesServiceDep,
) -> list[CandidateInboundRead | EmployerInboundRead]:
    return await service.inbound_for_user(user)


@router.post(
    "/inbound/companies/{company_id}/respond",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Candidate: like back a company that liked you",
)
async def respond_company(
    user: CandidateUser,
    company_id: uuid.UUID,
    service: ResponsesServiceDep,
    vacancy_id: Annotated[uuid.UUID | None, Query(alias="vacancyId")] = None,
) -> None:
    await service.respond_candidate(
        user, InboundRespondCandidate(company_id=company_id, vacancy_id=vacancy_id)
    )


@router.post(
    "/inbound/candidates/{candidate_id}/respond",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Employer: like back a candidate who liked your vacancy",
)
async def respond_candidate_profile(
    user: EmployerUser,
    candidate_id: uuid.UUID,
    service: ResponsesServiceDep,
    vacancy_id: Annotated[uuid.UUID | None, Query(alias="vacancyId")] = None,
) -> None:
    await service.respond_employer(
        user, InboundRespondEmployer(candidate_id=candidate_id, vacancy_id=vacancy_id)
    )
