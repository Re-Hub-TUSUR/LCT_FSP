from fastapi import APIRouter, status

from app.api.stub import not_implemented
from app.dependencies.auth import CandidateUser
from app.dependencies.common import PaginationDep
from app.schemas.application import ApplicationCreate, ApplicationRead
from app.schemas.common import Page

# Candidate-initiated responses are secondary to invitations (optional for MVP per ТЗ).
router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", status_code=status.HTTP_201_CREATED, summary="Candidate applies to a vacancy")
async def apply(_: CandidateUser, data: ApplicationCreate) -> ApplicationRead:
    not_implemented("applications.create")


@router.get("/me", summary="Candidate: own applications and their statuses")
async def list_my_applications(
    _: CandidateUser, pagination: PaginationDep
) -> Page[ApplicationRead]:
    not_implemented("applications.list_me")
