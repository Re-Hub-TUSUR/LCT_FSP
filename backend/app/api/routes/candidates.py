import uuid
from dataclasses import replace
from typing import Annotated

from fastapi import APIRouter, Query, Response, UploadFile, status

from app.dependencies.auth import CandidateUser, CurrentUser, EmployerUser
from app.dependencies.common import PaginationDep
from app.dependencies.filters import CandidateSearchParamsDep
from app.dependencies.services import (
    CandidateProfileServiceDep,
    CandidateSearchServiceDep,
    FspLinkServiceDep,
    ReactionServiceDep,
    ResumeImportServiceDep,
)
from app.schemas.candidate import (
    CandidateFacets,
    CandidatePresets,
    CandidateProfileUpdate,
    CandidateRead,
    CandidateSearchPage,
    CandidateSearchUpdate,
    FspLinkRequest,
    OwnCandidateRead,
    ResumeCreate,
    ResumeDraft,
)
from app.schemas.reaction import (
    CandidateReactionRequest,
    FeedView,
    ReactionCounts,
    ReactionRead,
)
from app.search.base import CandidateSort
from app.services.uploads import PHOTO_LIMIT, RESUME_LIMIT

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get(
    "",
    summary="Employer: search the categorised candidate bank",
    description=(
        "Full-text search runs on Elasticsearch (Russian morphology, IT slang, typos) with a "
        "database fallback; `engine` tells which one answered. Hidden and uncategorised profiles "
        "never appear; contacts are never returned here. Ranking: with `vacancyId` — fit to "
        "that vacancy, otherwise profile strength (test result + FSP results); candidates with "
        "more `nice` technologies go first."
    ),
)
async def search_candidates(
    *,
    user: EmployerUser,
    pagination: PaginationDep,
    search: CandidateSearchServiceDep,
    params: CandidateSearchParamsDep,
    vacancy_id: Annotated[uuid.UUID | None, Query(alias="vacancyId")] = None,
    sort: CandidateSort = "relevance",
) -> CandidateSearchPage:
    return await search.search(user, replace(params, vacancy_id=vacancy_id, sort=sort), pagination)


@router.get(
    "/facets",
    summary="Employer: how many candidates each filter option would leave",
    description=(
        "Takes the parameters of the search. An option's count is the list's total after "
        "choosing it alone in its group (a city: without relocation), the other filters staying "
        "as they are. `stack` counts the matching candidates per technology. When nobody "
        "matches, `relaxations` names up to three filters to loosen."
    ),
)
async def candidate_facets(
    user: EmployerUser, search: CandidateSearchServiceDep, params: CandidateSearchParamsDep
) -> CandidateFacets:
    return await search.facets(user, params)


@router.get(
    "/presets",
    summary="Employer: own vacancies as ready-made filters",
    description="Selecting a vacancy in the search fills the filters in from its requirements.",
)
async def candidate_presets(
    user: EmployerUser, search: CandidateSearchServiceDep, view: FeedView = "all"
) -> CandidatePresets:
    return await search.presets(user, view=view)


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


@router.patch(
    "/me/searching",
    summary="Job status: actively looking, open to offers, or not looking (hidden from search)",
    description="`searching` (true = open, false = not looking) is still accepted.",
)
async def update_searching(
    user: CandidateUser, data: CandidateSearchUpdate, profiles: CandidateProfileServiceDep
) -> OwnCandidateRead:
    return await profiles.set_searching(user, data.status())


@router.post(
    "/me/resume",
    summary="Recognise the fields of a PDF or DOCX resume (up to 5 MB). Nothing is saved",
)
async def upload_resume(
    _: CandidateUser, file: UploadFile, resumes: ResumeImportServiceDep
) -> ResumeDraft:
    return await resumes.draft(await file.read(RESUME_LIMIT + 1))


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


@router.post(
    "/me/fsp-link",
    summary="Finish the FSP ID sign-in: link the participant and import the registry history",
    description=(
        "`code` and `state` are the query parameters FSP ID appended to the callback page "
        "(start with `POST /fsp-id/authorize`). 409 when the participant is linked to another "
        "account. When the registry is down the link is kept and `fspSyncError` is set."
    ),
)
async def link_fsp(
    user: CandidateUser, data: FspLinkRequest, fsp: FspLinkServiceDep
) -> OwnCandidateRead:
    return await fsp.link(user, code=data.code, state=data.state)


@router.post("/me/fsp-sync", summary="Import the FSP registry history again")
async def sync_fsp(user: CandidateUser, fsp: FspLinkServiceDep) -> OwnCandidateRead:
    return await fsp.resync(user)


@router.delete("/me/fsp-link", summary="Unlink FSP ID and drop the imported results and titles")
async def unlink_fsp(user: CandidateUser, fsp: FspLinkServiceDep) -> OwnCandidateRead:
    return await fsp.unlink(user)


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
