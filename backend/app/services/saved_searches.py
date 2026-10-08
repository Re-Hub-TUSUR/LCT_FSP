"""Saved searches: filters to come back to, the results that are new since, and alerts.

A result is new while the search finds it and it was not shown when the search was last opened,
so a candidate counts as new whatever brought them in: a sign-up, a passed test, lower
expectations. A background check announces every new result once over the SSE stream.
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.errors import ConflictError, NotFoundError
from app.models import SavedSearch, User
from app.models.enums import SavedSearchKind
from app.repositories.candidate import CandidateRepository
from app.repositories.company import CompanyRepository
from app.repositories.reaction import ReactionRepository
from app.repositories.saved_search import SavedSearchRepository
from app.repositories.user import UserRepository
from app.repositories.vacancy import VacancyRepository
from app.schemas.saved_search import (
    CandidateSearchSave,
    SavedCandidateSearch,
    SavedVacancySearch,
    VacancySearchSave,
)
from app.search.elastic import ElasticSearchState
from app.services.candidate_search import CandidateSearchParams, CandidateSearchService
from app.services.categories import (
    BENEFIT_LABELS,
    EMPLOYMENT_LABELS,
    GRADE_LABELS,
    SPECIALIZATIONS,
    WORK_FORMAT_LABELS,
)
from app.services.matching import rub
from app.services.notifications import NotificationHub
from app.services.vacancy_feed import VacancyFeedParams, VacancyFeedService

logger = logging.getLogger(__name__)

MAX_SAVED_SEARCHES: Final = 20
# Values of one filter a title names before «+N».
LISTED: Final = 3


def _listed(values: Sequence[str], limit: int = LISTED) -> str:
    shown = ", ".join(values[:limit])
    return f"{shown} +{len(values) - limit}" if len(values) > limit else shown


def _salary(minimum: int | None, maximum: int | None) -> str | None:
    if minimum and maximum:
        return f"{rub(minimum)} – {rub(maximum)}"
    if minimum:
        return f"от {rub(minimum)}"
    if maximum:
        return f"до {rub(maximum)}"
    return None


def _years(count: int) -> str:
    tens, units = count % 100, count % 10
    if units == 1 and tens != 11:  # noqa: PLR2004 - Russian plural rules
        return "года"
    return "лет"


def _line(parts: Sequence[str | None]) -> str:
    return " · ".join(part for part in parts if part)


def candidate_search_text(search: CandidateSearchSave) -> tuple[str, str]:
    """A name and a one-line summary of a recruiter's search, made of its filters."""
    filters = search.filters
    text = search.text.strip() if search.text else ""
    title = _line(
        [
            f"«{text}»" if text else None,
            _listed([SPECIALIZATIONS.get(code, code) for code in filters.specializations], 2),
            " / ".join(GRADE_LABELS[grade] for grade in filters.grades),
            _listed(filters.stack),
        ]
    )
    summary = _line(
        [
            " / ".join(WORK_FORMAT_LABELS[fmt] for fmt in filters.work_formats),
            _listed(filters.cities, 2),
            _salary(filters.salary_min, filters.salary_max),
            "грейд подтверждён тестом" if filters.verified_only else None,
            "есть результаты ФСП" if filters.has_fsp else None,
            f"стаж от {filters.experience_min} {_years(filters.experience_min)}"
            if filters.experience_min
            else None,
            ", ".join(EMPLOYMENT_LABELS[kind] for kind in filters.employment_types),
            f"плюсом: {_listed(filters.nice)}" if filters.nice else None,
        ]
    )
    return title or "Все кандидаты", summary or "Без других фильтров"


def vacancy_search_text(search: VacancySearchSave) -> tuple[str, str]:
    """A name and a one-line summary of a candidate's search, made of its filters."""
    filters = search.filters
    title = _line(
        [
            " / ".join(WORK_FORMAT_LABELS[fmt] for fmt in filters.work_formats),
            f"от {rub(filters.salary_min)}" if filters.salary_min else None,
            _listed(filters.stack),
        ]
    )
    summary = _line(
        [
            "по профилю" if search.mode == "profile" else "все вакансии",
            _listed(filters.cities, 2),
            ", ".join(EMPLOYMENT_LABELS[kind] for kind in filters.employment_types),
            ", ".join(BENEFIT_LABELS[benefit] for benefit in filters.benefits),
            "аккредитованные IT-компании" if filters.accredited else None,
            f"плюсом: {_listed(filters.nice)}" if filters.nice else None,
        ]
    )
    fallback = "Вакансии по профилю" if search.mode == "profile" else "Все вакансии"
    return title or fallback, summary


def _ids(found: set[uuid.UUID]) -> list[str]:
    return sorted(str(item) for item in found)


def _new_count(row: SavedSearch, found: set[uuid.UUID]) -> int:
    seen = set(row.seen_ids)
    return sum(str(item) not in seen for item in found)


def _candidate_params(search: CandidateSearchSave) -> CandidateSearchParams:
    return CandidateSearchParams(filters=search.filters, text=search.text)


def _vacancy_params(search: VacancySearchSave) -> VacancyFeedParams:
    return VacancyFeedParams(mode=search.mode, filters=search.filters)


@dataclass(frozen=True, slots=True)
class SavedSearchAlert:
    user_id: uuid.UUID
    search_id: uuid.UUID
    kind: SavedSearchKind
    title: str
    # Results not shown since the search was last opened.
    new_count: int

    def event(self) -> dict[str, object]:
        return {
            "type": "saved_search_new",
            "searchId": str(self.search_id),
            "kind": self.kind.value,
            "title": self.title,
            "count": self.new_count,
        }


class SavedSearchService:
    def __init__(
        self,
        searches: SavedSearchRepository,
        candidates: CandidateSearchService,
        vacancies: VacancyFeedService,
    ) -> None:
        self._searches = searches
        self._candidates = candidates
        self._vacancies = vacancies

    # --- the recruiter's searches of candidates -------------------------------------------------

    async def candidate_searches(self, user: User) -> list[SavedCandidateSearch]:
        rows = await self._searches.for_user(user.id, SavedSearchKind.CANDIDATES)
        saved = [CandidateSearchSave.model_validate(row.params) for row in rows]
        found = await self._candidates.matching_ids(user, [_candidate_params(s) for s in saved])
        return [
            self._candidate_read(row, search, ids)
            for row, search, ids in zip(rows, saved, found, strict=True)
        ]

    async def save_candidate_search(
        self, user: User, data: CandidateSearchSave
    ) -> SavedCandidateSearch:
        """What the list shows now is seen already: only later results count as new."""
        await self._make_room(user)
        if data.vacancy_id is not None:
            await self._candidates.check_vacancy(user, data.vacancy_id)
        [found] = await self._candidates.matching_ids(user, [_candidate_params(data)])
        title, _ = candidate_search_text(data)
        row = await self._add(
            user,
            SavedSearchKind.CANDIDATES,
            data.title or title,
            data.model_dump(mode="json"),
            found,
        )
        return self._candidate_read(row, data, found)

    async def open_candidate_search(self, user: User, search_id: uuid.UUID) -> SavedCandidateSearch:
        """The recruiter opens the search: everything it finds now is seen."""
        row = await self._own(user, search_id, SavedSearchKind.CANDIDATES)
        search = CandidateSearchSave.model_validate(row.params)
        [found] = await self._candidates.matching_ids(user, [_candidate_params(search)])
        self._mark_seen(row, found)
        return self._candidate_read(row, search, found)

    # --- the candidate's searches of vacancies --------------------------------------------------

    async def vacancy_searches(self, user: User) -> list[SavedVacancySearch]:
        rows = await self._searches.for_user(user.id, SavedSearchKind.VACANCIES)
        saved = [VacancySearchSave.model_validate(row.params) for row in rows]
        found = await self._vacancies.matching_ids(user, [_vacancy_params(s) for s in saved])
        return [
            self._vacancy_read(row, search, ids)
            for row, search, ids in zip(rows, saved, found, strict=True)
        ]

    async def save_vacancy_search(self, user: User, data: VacancySearchSave) -> SavedVacancySearch:
        await self._make_room(user)
        [found] = await self._vacancies.matching_ids(user, [_vacancy_params(data)])
        title, _ = vacancy_search_text(data)
        row = await self._add(
            user,
            SavedSearchKind.VACANCIES,
            data.title or title,
            data.model_dump(mode="json"),
            found,
        )
        return self._vacancy_read(row, data, found)

    async def open_vacancy_search(self, user: User, search_id: uuid.UUID) -> SavedVacancySearch:
        row = await self._own(user, search_id, SavedSearchKind.VACANCIES)
        search = VacancySearchSave.model_validate(row.params)
        [found] = await self._vacancies.matching_ids(user, [_vacancy_params(search)])
        self._mark_seen(row, found)
        return self._vacancy_read(row, search, found)

    async def delete(self, user: User, search_id: uuid.UUID, kind: SavedSearchKind) -> None:
        await self._searches.delete(await self._own(user, search_id, kind))

    # --- alerts ---------------------------------------------------------------------------------

    async def new_results(self, users: UserRepository) -> list[SavedSearchAlert]:
        """Searches with results nobody announced yet; those results are marked announced, so
        every new result comes up once."""
        by_user: defaultdict[uuid.UUID, list[SavedSearch]] = defaultdict(list)
        for row in await self._searches.all():
            by_user[row.user_id].append(row)
        alerts: list[SavedSearchAlert] = []
        for user_id, rows in by_user.items():
            user = await users.get_by_id(user_id)
            if user is None:
                continue
            try:
                found = await self._found(user, rows)
            except Exception:
                logger.exception("Saved searches of user %s were not checked", user_id)
                continue
            for row, ids in zip(rows, found, strict=True):
                current = set(_ids(ids))
                fresh = current - set(row.seen_ids) - set(row.notified_ids)
                if not fresh:
                    continue
                row.notified_ids = sorted(set(row.notified_ids) | fresh)
                alerts.append(
                    SavedSearchAlert(user_id, row.id, row.kind, row.title, _new_count(row, ids))
                )
        return alerts

    async def _found(self, user: User, rows: Sequence[SavedSearch]) -> list[set[uuid.UUID]]:
        """What each of a user's searches finds now, in the order of `rows`."""
        found: dict[uuid.UUID, set[uuid.UUID]] = {}
        candidates = [row for row in rows if row.kind == SavedSearchKind.CANDIDATES]
        if candidates:
            params = [
                _candidate_params(CandidateSearchSave.model_validate(row.params))
                for row in candidates
            ]
            for row, ids in zip(
                candidates, await self._candidates.matching_ids(user, params), strict=True
            ):
                found[row.id] = ids
        vacancies = [row for row in rows if row.kind == SavedSearchKind.VACANCIES]
        if vacancies:
            params_v = [
                _vacancy_params(VacancySearchSave.model_validate(row.params)) for row in vacancies
            ]
            for row, ids in zip(
                vacancies, await self._vacancies.matching_ids(user, params_v), strict=True
            ):
                found[row.id] = ids
        return [found[row.id] for row in rows]

    # --- helpers --------------------------------------------------------------------------------

    async def _make_room(self, user: User) -> None:
        if await self._searches.count_for_user(user.id) >= MAX_SAVED_SEARCHES:
            msg = f"Можно сохранить не больше {MAX_SAVED_SEARCHES} поисков: удалите ненужный"
            raise ConflictError(msg)

    async def _own(self, user: User, search_id: uuid.UUID, kind: SavedSearchKind) -> SavedSearch:
        row = await self._searches.get(search_id)
        if row is None or row.user_id != user.id or row.kind != kind:
            raise NotFoundError("Сохранённый поиск не найден")
        return row

    async def _add(
        self,
        user: User,
        kind: SavedSearchKind,
        title: str,
        params: dict[str, object],
        found: set[uuid.UUID],
    ) -> SavedSearch:
        params.pop("title", None)
        now = datetime.now(UTC)
        return await self._searches.add(
            SavedSearch(
                user_id=user.id,
                kind=kind,
                title=title,
                params=params,
                seen_ids=_ids(found),
                notified_ids=[],
                seen_at=now,
                created_at=now,
            )
        )

    @staticmethod
    def _mark_seen(row: SavedSearch, found: set[uuid.UUID]) -> None:
        row.seen_ids = _ids(found)
        row.notified_ids = []
        row.seen_at = datetime.now(UTC)

    @staticmethod
    def _candidate_read(
        row: SavedSearch, search: CandidateSearchSave, found: set[uuid.UUID]
    ) -> SavedCandidateSearch:
        _, summary = candidate_search_text(search)
        return SavedCandidateSearch(
            id=row.id,
            title=row.title,
            summary=summary,
            filters=search.filters,
            text=search.text,
            vacancy_id=search.vacancy_id,
            count=len(found),
            new_count=_new_count(row, found),
            created_at=row.created_at,
        )

    @staticmethod
    def _vacancy_read(
        row: SavedSearch, search: VacancySearchSave, found: set[uuid.UUID]
    ) -> SavedVacancySearch:
        _, summary = vacancy_search_text(search)
        return SavedVacancySearch(
            id=row.id,
            title=row.title,
            summary=summary,
            mode=search.mode,
            filters=search.filters,
            count=len(found),
            new_count=_new_count(row, found),
            created_at=row.created_at,
        )


def saved_search_service(
    session: AsyncSession, elastic: ElasticSearchState | None
) -> SavedSearchService:
    candidates = CandidateSearchService(
        CandidateRepository(session),
        VacancyRepository(session),
        CompanyRepository(session),
        ReactionRepository(session),
        elastic,
    )
    vacancies = VacancyFeedService(
        VacancyRepository(session), CandidateRepository(session), ReactionRepository(session)
    )
    return SavedSearchService(SavedSearchRepository(session), candidates, vacancies)


async def announce_new_results(
    sessions: async_sessionmaker[AsyncSession],
    hub: NotificationHub,
    elastic: ElasticSearchState | None,
) -> int:
    """Checks every saved search once and tells the users about new results."""
    async with sessions() as session:
        alerts = await saved_search_service(session, elastic).new_results(UserRepository(session))
        await session.commit()
    for alert in alerts:
        await hub.publish(alert.user_id, alert.event())
    return len(alerts)


async def run_alerts(
    interval: timedelta,
    sessions: async_sessionmaker[AsyncSession],
    hub: NotificationHub,
    elastic: ElasticSearchState | None,
) -> None:
    """The background check of the API process, every `interval` until cancelled."""
    while True:
        await asyncio.sleep(interval.total_seconds())
        try:
            await announce_new_results(sessions, hub, elastic)
        except Exception:
            logger.exception("Saved search alerts failed; the next check tries again")
