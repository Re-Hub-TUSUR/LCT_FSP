import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.stub import not_implemented
from app.dependencies.auth import CandidateUser, EmployerUser, OptionalUser
from app.dependencies.common import PaginationDep
from app.dependencies.filters import VacancyFeedParamsDep
from app.dependencies.services import (
    ReactionServiceDep,
    VacancyFeedServiceDep,
    VacancyServiceDep,
)
from app.models.enums import Grade, WorkFormat
from app.schemas.common import Page
from app.schemas.reaction import FeedView, ReactionCounts, ReactionRead, ReactionRequest
from app.schemas.vacancy import (
    VacancyCreate,
    VacancyFacets,
    VacancyFeedPage,
    VacancyFeedPresets,
    VacancyRead,
)

router = APIRouter(prefix="/vacancies", tags=["vacancies"])


@router.get("", summary="Published vacancies, newest first (public list)")
async def list_vacancies(
    *,
    pagination: PaginationDep,
    vacancies: VacancyServiceDep,
    search: Annotated[str | None, Query(max_length=200)] = None,
    specialization: str | None = None,
    grade: Grade | None = None,
    work_format: Annotated[WorkFormat | None, Query(alias="workFormat")] = None,
) -> Page[VacancyRead]:
    return await vacancies.public_page(
        specialization=specialization,
        grade=grade,
        work_format=work_format,
        search=search,
        pagination=pagination,
    )


@router.get(
    "/feed",
    summary="Candidate: relevant vacancies ranked by fit to the profile, with reasons",
    description=(
        "`mode=profile`: only the candidate's and related specializations, the same or a "
        "neighbouring grade, best fit first; `mode=free`: every vacancy, newest first. Vacancies "
        "asking for more `nice` technologies go first. `view=all` hides skipped cards, `unseen` "
        "hides every decided card (swipe deck). `liked`, `matched` and `skipped` are the "
        "candidate's own decisions, the latest first, whatever the profile says now; `matched` = "
        "liked and liked back by the recruiter."
    ),
)
async def vacancy_feed(
    user: CandidateUser,
    pagination: PaginationDep,
    feed: VacancyFeedServiceDep,
    params: VacancyFeedParamsDep,
) -> VacancyFeedPage:
    return await feed.feed(user, params, pagination)


@router.get(
    "/feed/facets",
    summary="Candidate: how many vacancies each filter option would leave",
    description=(
        "Takes the parameters of the feed. A format, an employment type or a condition counts "
        "the feed after adding it to the chosen ones; `cities` and `stack` count the vacancies "
        "of the mode. When nothing matches, `relaxations` names up to three filters to loosen."
    ),
)
async def vacancy_feed_facets(
    user: CandidateUser, feed: VacancyFeedServiceDep, params: VacancyFeedParamsDep
) -> VacancyFacets:
    return await feed.facets(user, params)


@router.get(
    "/feed/presets",
    summary="Candidate: the feed's modes and the filters the profile fills in",
)
async def vacancy_feed_presets(
    user: CandidateUser, feed: VacancyFeedServiceDep, view: FeedView = "all"
) -> VacancyFeedPresets:
    return await feed.presets(user, view=view)


@router.get(
    "/reactions/counts",
    summary="Candidate: how many vacancies are liked, matched and skipped",
)
async def vacancy_reaction_counts(
    user: CandidateUser, feed: VacancyFeedServiceDep
) -> ReactionCounts:
    return await feed.counts(user)


@router.get("/mine", summary="Employer: own company's vacancies, drafts first")
async def my_vacancies(
    user: EmployerUser, pagination: PaginationDep, vacancies: VacancyServiceDep
) -> Page[VacancyRead]:
    return await vacancies.mine(user, pagination)


@router.post("", status_code=status.HTTP_201_CREATED, summary="Publish a vacancy")
async def create_vacancy(_: EmployerUser, data: VacancyCreate) -> VacancyRead:
    not_implemented("vacancies.create")


@router.get("/{vacancy_id}", summary="Vacancy details (a draft only for its company)")
async def read_vacancy(
    vacancy_id: uuid.UUID, viewer: OptionalUser, vacancies: VacancyServiceDep
) -> VacancyRead:
    return await vacancies.read(vacancy_id, viewer)


@router.patch("/{vacancy_id}", summary="Edit own vacancy")
async def update_vacancy(
    vacancy_id: uuid.UUID, _: EmployerUser, data: VacancyCreate
) -> VacancyRead:
    not_implemented("vacancies.update")


@router.put("/{vacancy_id}/reaction", summary="Candidate: like (favourites) or skip a vacancy")
async def react_to_vacancy(
    vacancy_id: uuid.UUID,
    data: ReactionRequest,
    user: CandidateUser,
    reactions: ReactionServiceDep,
) -> ReactionRead:
    reaction = await reactions.react_to_vacancy(user, vacancy_id, data.kind)
    return ReactionRead.model_validate(reaction)


@router.delete(
    "/{vacancy_id}/reaction",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Candidate: undo a like or a skip",
)
async def clear_vacancy_reaction(
    vacancy_id: uuid.UUID, user: CandidateUser, reactions: ReactionServiceDep
) -> Response:
    await reactions.clear_vacancy(user, vacancy_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
