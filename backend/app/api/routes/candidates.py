import uuid
from typing import Annotated

from fastapi import APIRouter, Query, UploadFile, status

from app.api.stub import not_implemented
from app.dependencies.auth import CandidateUser, CurrentUser, EmployerUser
from app.dependencies.common import PaginationDep
from app.models.enums import Grade
from app.schemas.candidate import CandidateProfileUpdate, CandidateRead, FspLinkRequest
from app.schemas.common import Page

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("", summary="Employer search over the categorised candidate bank")
async def search_candidates(
    _: EmployerUser,
    pagination: PaginationDep,
    specialization: str | None = None,
    grade: Grade | None = None,
    stack: Annotated[list[str] | None, Query()] = None,
    has_fsp_achievements: Annotated[bool | None, Query(alias="hasFspAchievements")] = None,
) -> Page[CandidateRead]:
    # Ranking inside a category: assessment score first, confirmed FSP achievements next.
    not_implemented("candidates.search")


@router.get("/me", summary="Own candidate profile")
async def read_my_profile(_: CandidateUser) -> CandidateRead:
    not_implemented("candidates.read_me")


@router.patch("/me", summary="Update own profile (manual resume form)")
async def update_my_profile(_: CandidateUser, data: CandidateProfileUpdate) -> CandidateRead:
    not_implemented("candidates.update_me")


@router.post(
    "/me/resume",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a PDF resume for automatic field recognition",
)
async def upload_resume(_: CandidateUser, file: UploadFile) -> CandidateRead:
    not_implemented("candidates.upload_resume")


@router.post("/me/fsp-link", summary="Link the profile to an FSP participant ID")
async def link_fsp(_: CandidateUser, data: FspLinkRequest) -> CandidateRead:
    not_implemented("candidates.link_fsp")


@router.get("/{candidate_id}", summary="Public candidate profile (contacts only when allowed)")
async def read_candidate(candidate_id: uuid.UUID, _: CurrentUser) -> CandidateRead:
    not_implemented("candidates.read")
