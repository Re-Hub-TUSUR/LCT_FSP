import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.candidate import CandidateFilterSet
from app.schemas.common import ApiModel
from app.schemas.vacancy import FeedMode, VacancyFilterSet


class CandidateSearchSave(ApiModel):
    """The recruiter's search as the list shows it now; without a title one is made up."""

    title: str | None = Field(default=None, max_length=120)
    filters: CandidateFilterSet = Field(default_factory=CandidateFilterSet)
    text: str | None = Field(default=None, max_length=200)
    # Hiring for this own vacancy: the results are ranked by fit to it.
    vacancy_id: uuid.UUID | None = None


class SavedCandidateSearch(ApiModel):
    id: uuid.UUID
    title: str
    # The rest of the filters in a line, e.g. «Удалённо · до 240 000 ₽».
    summary: str
    filters: CandidateFilterSet
    text: str | None
    vacancy_id: uuid.UUID | None
    # Candidates the search finds now, and the ones not shown when it was last opened.
    count: int
    new_count: int
    created_at: datetime


class VacancySearchSave(ApiModel):
    """The candidate's feed as it is now; without a title one is made up."""

    title: str | None = Field(default=None, max_length=120)
    mode: FeedMode = "profile"
    filters: VacancyFilterSet = Field(default_factory=VacancyFilterSet)


class SavedVacancySearch(ApiModel):
    id: uuid.UUID
    title: str
    summary: str
    mode: FeedMode
    filters: VacancyFilterSet
    # Vacancies the search finds now, and the ones not shown when it was last opened.
    count: int
    new_count: int
    created_at: datetime
