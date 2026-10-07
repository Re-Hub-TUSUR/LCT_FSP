"""Query parameters of the feeds' filters, shared by a list and the counts next to its filters."""

from typing import Annotated

from fastapi import Depends, Query
from pydantic import StringConstraints

from app.models.enums import (
    EmploymentType,
    FspDiscipline,
    FspResult,
    Grade,
    JobStatus,
    VacancyBenefit,
    WorkFormat,
)
from app.schemas.candidate import CandidateFilterSet
from app.schemas.reaction import FeedView
from app.schemas.vacancy import FeedMode, VacancyFilterSet
from app.services.candidate_search import CandidateSearchParams
from app.services.vacancy_feed import VacancyFeedParams

MAX_TERMS = 30

# Technologies, cities and specialization codes typed or picked in the filters.
Term = Annotated[str, StringConstraints(max_length=100)]
Terms = list[Term] | None


def get_candidate_search_params(
    *,
    q: Annotated[str | None, Query(max_length=200)] = None,
    specialization: Annotated[Terms, Query(max_length=MAX_TERMS)] = None,
    grade: Annotated[list[Grade] | None, Query()] = None,
    verified_only: Annotated[bool, Query(alias="verifiedOnly")] = False,
    has_fsp: Annotated[bool | None, Query(alias="hasFspAchievements")] = None,
    fsp_result: Annotated[
        FspResult | None, Query(alias="fspResult", description="Не ниже этого результата")
    ] = None,
    fsp_discipline: Annotated[FspDiscipline | None, Query(alias="fspDiscipline")] = None,
    experience_min: Annotated[int | None, Query(alias="experienceMin", ge=0, le=60)] = None,
    stack: Annotated[
        Terms, Query(max_length=MAX_TERMS, description="Обязательно: каждая технология")
    ] = None,
    nice: Annotated[
        Terms, Query(max_length=MAX_TERMS, description="Будет плюсом: поднимает выше")
    ] = None,
    salary_min: Annotated[int | None, Query(alias="salaryMin", gt=0)] = None,
    salary_max: Annotated[int | None, Query(alias="salaryMax", gt=0)] = None,
    work_format: Annotated[list[WorkFormat] | None, Query(alias="workFormat")] = None,
    city: Annotated[Terms, Query(max_length=MAX_TERMS, description="Для офиса и гибрида")] = None,
    relocation: Annotated[
        bool, Query(description="Учитывать готовых к переезду в другие города")
    ] = True,
    employment: Annotated[list[EmploymentType] | None, Query()] = None,
    job_status: Annotated[list[JobStatus] | None, Query(alias="jobStatus")] = None,
    active_days: Annotated[
        int | None, Query(alias="activeDays", ge=1, le=365, description="Заходил за N дней")
    ] = None,
    view: FeedView = "all",
) -> CandidateSearchParams:
    filters = CandidateFilterSet(
        specializations=specialization or [],
        grades=grade or [],
        verified_only=verified_only,
        has_fsp=has_fsp,
        fsp_result=fsp_result,
        fsp_discipline=fsp_discipline,
        experience_min=experience_min,
        stack=stack or [],
        nice=nice or [],
        salary_min=salary_min,
        salary_max=salary_max,
        work_formats=work_format or [],
        cities=city or [],
        relocation=relocation,
        employment_types=employment or [],
        job_statuses=job_status or [],
        active_days=active_days,
    )
    return CandidateSearchParams(filters=filters, text=q, view=view)


CandidateSearchParamsDep = Annotated[CandidateSearchParams, Depends(get_candidate_search_params)]


def get_vacancy_feed_params(
    *,
    mode: Annotated[
        FeedMode, Query(description="profile — по профилю и совпадению, free — все по дате")
    ] = "profile",
    salary_min: Annotated[int | None, Query(alias="salaryMin", ge=0)] = None,
    work_format: Annotated[list[WorkFormat] | None, Query(alias="workFormat")] = None,
    city: Annotated[Terms, Query(max_length=MAX_TERMS, description="Для офиса и гибрида")] = None,
    relocation: Annotated[
        bool, Query(description="Добавить вакансии других городов с помощью при переезде")
    ] = False,
    employment: Annotated[list[EmploymentType] | None, Query()] = None,
    stack: Annotated[
        Terms, Query(max_length=MAX_TERMS, description="Обязательно: каждая технология")
    ] = None,
    nice: Annotated[
        Terms, Query(max_length=MAX_TERMS, description="Будет плюсом: поднимает выше")
    ] = None,
    benefit: Annotated[list[VacancyBenefit] | None, Query()] = None,
    accredited: Annotated[bool, Query(description="Аккредитованная IT-компания")] = False,
    view: FeedView = "all",
) -> VacancyFeedParams:
    filters = VacancyFilterSet(
        salary_min=salary_min or None,
        work_formats=work_format or [],
        cities=city or [],
        relocation=relocation,
        employment_types=employment or [],
        stack=stack or [],
        nice=nice or [],
        benefits=benefit or [],
        accredited=accredited,
    )
    return VacancyFeedParams(mode=mode, filters=filters, view=view)


VacancyFeedParamsDep = Annotated[VacancyFeedParams, Depends(get_vacancy_feed_params)]
