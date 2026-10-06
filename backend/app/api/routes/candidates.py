import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response, UploadFile, status

from app.api.stub import not_implemented
from app.dependencies.auth import CandidateUser, CurrentUser, EmployerUser
from app.dependencies.common import PaginationDep
from app.dependencies.services import (
    CandidateProfileServiceDep,
    CandidateSearchServiceDep,
    ReactionServiceDep,
)
from app.models.enums import Grade, WorkFormat
from app.schemas.candidate import (
    CandidateProfileUpdate,
    CandidateRead,
    CandidateSearchPage,
    CandidateSearchUpdate,
    FspLinkRequest,
    OwnCandidateRead,
    ResumeCreate,
)
from app.schemas.reaction import (
    CandidateReactionRequest,
    FeedView,
    ReactionCounts,
    ReactionRead,
)
from app.search.base import CandidateSort
from app.services.candidate_search import CandidateSearchParams
from app.services.uploads import PHOTO_LIMIT

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get(
    "",
    summary="Employer: search the categorised candidate bank",
    description=(
        "Full-text search runs on Elasticsearch (Russian morphology, IT slang, typos) with a "
        "database fallback; `engine` tells which one answered. Hidden and uncategorised profiles "
        "never appear; contacts are never returned here. Ranking: with `vacancyId` — fit to "
        "that vacancy, otherwise profile strength (test result + FSP results)."
    ),
)
async def search_candidates(
    *,
    user: EmployerUser,
    pagination: PaginationDep,
    search: CandidateSearchServiceDep,
    q: Annotated[str | None, Query(max_length=200)] = None,
    specialization: str | None = None,
    grade: Annotated[list[Grade] | None, Query()] = None,
    stack: Annotated[list[str] | None, Query()] = None,
    has_fsp_achievements: Annotated[bool | None, Query(alias="hasFspAchievements")] = None,
    verified_only: Annotated[bool, Query(alias="verifiedOnly")] = False,
    work_format: Annotated[list[WorkFormat] | None, Query(alias="workFormat")] = None,
    city: Annotated[str | None, Query(max_length=100)] = None,
    salary_max: Annotated[int | None, Query(alias="salaryMax", gt=0)] = None,
    experience_min: Annotated[int | None, Query(alias="experienceMin", ge=0, le=60)] = None,
    vacancy_id: Annotated[uuid.UUID | None, Query(alias="vacancyId")] = None,
    view: FeedView = "all",
    sort: CandidateSort = "relevance",
) -> CandidateSearchPage:
    params = CandidateSearchParams(
        text=q,
        specialization=specialization,
        grades=tuple(grade or ()),
        stack=tuple(stack or ()),
        has_fsp=has_fsp_achievements,
        verified_only=verified_only,
        work_formats=tuple(work_format or ()),
        city=city,
        salary_max=salary_max,
        experience_min=experience_min,
        vacancy_id=vacancy_id,
        view=view,
        sort=sort,
    )
    return await search.search(user, params, pagination)


@router.get(
    "/reactions/counts",
    summary="Employer: how many candidates are liked, matched and skipped",
)
async def candidate_reaction_counts(
    user: EmployerUser, search: CandidateSearchServiceDep
) -> ReactionCounts:
    return await search.counts(user)


@router.get("/me", summary="Own candidate profile")
async def read_my_profile(
    user: CandidateUser, profiles: CandidateProfileServiceDep
) -> OwnCandidateRead:
    return await profiles.read_own(user)


@router.patch("/me", summary="Create or update the resume. Does not set the grade.")
async def update_my_profile(
    user: CandidateUser, data: CandidateProfileUpdate, profiles: CandidateProfileServiceDep
) -> OwnCandidateRead:
    return await profiles.save_resume(user, data)


@router.patch("/me/searching", summary="Show or hide the profile in employer search")
async def update_searching(
    user: CandidateUser, data: CandidateSearchUpdate, profiles: CandidateProfileServiceDep
) -> OwnCandidateRead:
    return await profiles.set_searching(user, data.searching)


@router.post(
    "/me/resume",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a PDF resume for automatic field recognition",
)
async def upload_resume(_: CandidateUser, file: UploadFile) -> CandidateRead:
    not_implemented("candidates.upload_resume")


@router.post("/me/resumes", summary="Add a second profession profile. It is not the priority one.")
async def add_resume(
    user: CandidateUser, data: ResumeCreate, profiles: CandidateProfileServiceDep
) -> OwnCandidateRead:
    return await profiles.add_resume(user, data)


@router.post(
    "/me/resumes/{resume_id}/primary",
    summary="Make this resume the one employers and the feed see first",
)
async def make_resume_primary(
    resume_id: uuid.UUID, user: CandidateUser, profiles: CandidateProfileServiceDep
) -> OwnCandidateRead:
    return await profiles.make_primary(user, resume_id)


@router.post("/me/photo", summary="Upload a profile photo (JPEG, PNG or WebP, up to 2 MB)")
async def upload_photo(
    user: CandidateUser, file: UploadFile, profiles: CandidateProfileServiceDep
) -> OwnCandidateRead:
    return await profiles.set_photo(user, await file.read(PHOTO_LIMIT + 1))


@router.delete("/me/photo", summary="Remove the profile photo")
async def delete_photo(
    user: CandidateUser, profiles: CandidateProfileServiceDep
) -> OwnCandidateRead:
    return await profiles.clear_photo(user)


@router.get("/me/photo", summary="Own profile photo")
async def read_my_photo(user: CandidateUser, profiles: CandidateProfileServiceDep) -> Response:
    profile = await profiles.read_own(user)
    body, media = await profiles.open_photo(profile.id, user)
    return _photo_response(body, media)


@router.get("/{candidate_id}/photo", summary="Profile photo, when the viewer may see the profile")
async def read_candidate_photo(
    candidate_id: uuid.UUID, viewer: CurrentUser, profiles: CandidateProfileServiceDep
) -> Response:
    body, media = await profiles.open_photo(candidate_id, viewer)
    return _photo_response(body, media)


def _photo_response(body: bytes, media: str) -> Response:
    return Response(
        content=body,
        media_type=media,
        headers={
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": "inline",
            "Cache-Control": "private, max-age=300",
        },
    )


@router.post("/me/fsp-link", summary="Link the profile to an FSP participant ID")
async def link_fsp(
    user: CandidateUser, data: FspLinkRequest, profiles: CandidateProfileServiceDep
) -> OwnCandidateRead:
    return await profiles.link_fsp(user, data.fsp_member_id)


@router.delete("/me/fsp-link", summary="Unlink FSP and drop imported achievements")
async def unlink_fsp(user: CandidateUser, profiles: CandidateProfileServiceDep) -> OwnCandidateRead:
    return await profiles.unlink_fsp(user)


@router.get(
    "/{candidate_id}",
    summary="Candidate profile: the candidate themself or an employer (visible profiles only)",
    description="Contacts only for the candidate and an employer whose invitation was accepted.",
)
async def read_candidate(
    candidate_id: uuid.UUID, viewer: CurrentUser, profiles: CandidateProfileServiceDep
) -> CandidateRead:
    return await profiles.read(candidate_id, viewer)


@router.put(
    "/{candidate_id}/reaction", summary="Employer: add a candidate to favourites or skip them"
)
async def react_to_candidate(
    candidate_id: uuid.UUID,
    data: CandidateReactionRequest,
    user: EmployerUser,
    reactions: ReactionServiceDep,
) -> ReactionRead:
    reaction = await reactions.react_to_candidate(user, candidate_id, data.kind, data.vacancy_id)
    return ReactionRead.model_validate(reaction)


@router.delete(
    "/{candidate_id}/reaction",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Employer: undo a like or a skip",
)
async def clear_candidate_reaction(
    candidate_id: uuid.UUID, user: EmployerUser, reactions: ReactionServiceDep
) -> Response:
    await reactions.clear_candidate(user, candidate_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
