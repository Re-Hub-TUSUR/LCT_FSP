import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.dependencies.auth import CandidateUser, EmployerUser, OptionalUser
from app.dependencies.common import PaginationDep
from app.dependencies.filters import VacancyFeedParamsDep
from app.dependencies.services import (
    ReactionServiceDep,
    SavedSearchServiceDep,
    VacancyFeedServiceDep,
    VacancyServiceDep,
)
from app.models.enums import Grade, SavedSearchKind, WorkFormat
from app.schemas.common import Page
from app.schemas.reaction import FeedView, ReactionCounts, ReactionRead, ReactionRequest
from app.schemas.saved_search import SavedVacancySearch, VacancySearchSave
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
    company_id: Annotated[uuid.UUID | None, Query(alias="companyId")] = None,
) -> Page[VacancyRead]:
    return await vacancies.public_page(
        company_id=company_id,
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
    "/feed/saved-searches",
    summary="Candidate: saved searches with how many vacancies each finds and how many are new",
)
async def list_saved_vacancy_searches(
    user: CandidateUser, searches: SavedSearchServiceDep
) -> list[SavedVacancySearch]:
    return await searches.vacancy_searches(user)


@router.post(
    "/feed/saved-searches",
    status_code=status.HTTP_201_CREATED,
    summary="Candidate: save the current feed filters",
    description=(
        "The vacancies found now count as seen; later ones are new and come as a notification "
        "(`saved_search_new` in the notification stream). Up to 20 searches."
    ),
)
async def save_vacancy_search(
    data: VacancySearchSave, user: CandidateUser, searches: SavedSearchServiceDep
) -> SavedVacancySearch:
    return await searches.save_vacancy_search(user, data)


@router.post(
    "/feed/saved-searches/{search_id}/seen",
    summary="Candidate: the search was opened, every vacancy it finds now is seen",
)
async def open_saved_vacancy_search(
    search_id: uuid.UUID, user: CandidateUser, searches: SavedSearchServiceDep
) -> SavedVacancySearch:
    return await searches.open_vacancy_search(user, search_id)


@router.delete(
    "/feed/saved-searches/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Candidate: delete a saved search",
)
async def delete_saved_vacancy_search(
    search_id: uuid.UUID, user: CandidateUser, searches: SavedSearchServiceDep
) -> Response:
    await searches.delete(user, search_id, SavedSearchKind.VACANCIES)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Employer: publish a vacancy or save it as a draft (`publish: false`)",
)
async def create_vacancy(
    user: EmployerUser, data: VacancyCreate, vacancies: VacancyServiceDep
) -> VacancyRead:
    return await vacancies.create(user, data)


@router.get("/{vacancy_id}", summary="Vacancy details (a draft only for its company)")
async def read_vacancy(
    vacancy_id: uuid.UUID, viewer: OptionalUser, vacancies: VacancyServiceDep
) -> VacancyRead:
    return await vacancies.read(vacancy_id, viewer)


@router.patch(
    "/{vacancy_id}",
    summary="Employer: replace own vacancy; `publish` publishes a draft or takes it back",
)
async def update_vacancy(
    vacancy_id: uuid.UUID, user: EmployerUser, data: VacancyCreate, vacancies: VacancyServiceDep
) -> VacancyRead:
    return await vacancies.update(user, vacancy_id, data)


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
