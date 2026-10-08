"""Calendar: interviews a company schedules with candidates and the candidate's answer."""

import uuid
from datetime import UTC, datetime

from app.core.errors import AppError, ConflictError, NotFoundError
from app.models import Meeting, MeetingStatus, User, UserRole
from app.repositories.candidate import CandidateRepository
from app.repositories.company import CompanyRepository
from app.repositories.meeting import MeetingRepository
from app.repositories.vacancy import VacancyRepository
from app.schemas.calendar import CalendarEventRead, CalendarParty, MeetingCreate, MeetingUpdate
from app.services.notifications import NotificationHub, announce_meeting


def _utc(value: datetime) -> datetime:
    # SQLite (tests) returns naive datetimes; they are stored in UTC.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _event(
    meeting: Meeting, company_name: str, candidate_name: str, vacancy_title: str | None
) -> CalendarEventRead:
    vacancy = None
    if meeting.vacancy_id is not None and vacancy_title is not None:
        vacancy = CalendarParty(id=meeting.vacancy_id, name=vacancy_title)
    return CalendarEventRead(
        id=meeting.id,
        title=meeting.title,
        kind="interview",
        starts_at=_utc(meeting.starts_at),
        ends_at=_utc(meeting.ends_at),
        invitation_id=None,
        status=meeting.status,
        company=CalendarParty(id=meeting.company_id, name=company_name),
        candidate=CalendarParty(id=meeting.candidate_id, name=candidate_name),
        vacancy=vacancy,
        location=meeting.location,
        note=meeting.note,
    )


class CalendarService:
    def __init__(
        self,
        meetings: MeetingRepository,
        companies: CompanyRepository,
        candidates: CandidateRepository,
        vacancies: VacancyRepository,
        notifications: NotificationHub | None = None,
    ) -> None:
        self._meetings = meetings
        self._companies = companies
        self._candidates = candidates
        self._vacancies = vacancies
        self._notifications = notifications

    async def events(self, user: User, from_: datetime, to: datetime) -> list[CalendarEventRead]:
        """An employer sees the meetings of the company, a candidate — the ones they are in."""
        if to <= from_:
            raise AppError("Конец периода должен быть позже начала")
        company_id = candidate_id = None
        if user.role == UserRole.EMPLOYER:
            company = await self._companies.get_by_owner(user.id)
            company_id = company.id if company else None
        elif user.role == UserRole.CANDIDATE:
            profile = await self._candidates.get_by_user(user.id)
            candidate_id = profile.id if profile else None
        if company_id is None and candidate_id is None:
            return []
        rows = await self._meetings.in_range(
            starts_before=_utc(to),
            ends_after=_utc(from_),
            company_id=company_id,
            candidate_id=candidate_id,
        )
        return [_event(*row) for row in rows]

    async def schedule(self, user: User, data: MeetingCreate) -> CalendarEventRead:
        company = await self._companies.get_by_owner(user.id)
        if company is None:
            raise ConflictError("Сначала заполните профиль компании")
        profile = await self._candidates.get(data.candidate_id)
        if profile is None or not profile.is_visible_to_employers:
            raise NotFoundError("Кандидат не найден")
        starts_at, ends_at = _utc(data.starts_at), _utc(data.ends_at)
        await self._check_slot(company.id, starts_at, ends_at)
        vacancy_title = await self._own_vacancy_title(user, data.vacancy_id)

        meeting = await self._meetings.add(
            Meeting(
                company_id=company.id,
                candidate_id=profile.id,
                vacancy_id=data.vacancy_id,
                title=data.title.strip(),
                starts_at=starts_at,
                ends_at=ends_at,
                location=_clean(data.location),
                note=_clean(data.note),
                status=MeetingStatus.PENDING,
            )
        )
        await announce_meeting(
            self._notifications,
            user_id=profile.user_id,
            meeting_id=meeting.id,
            company_name=company.name,
            title=meeting.title,
            starts_at=starts_at,
        )
        return _event(meeting, company.name, profile.display_name, vacancy_title)

    async def reschedule(
        self, user: User, meeting_id: uuid.UUID, data: MeetingUpdate
    ) -> CalendarEventRead:
        meeting, company_name = await self._own_meeting(user, meeting_id)
        starts_at, ends_at = _utc(data.starts_at), _utc(data.ends_at)
        moved = (_utc(meeting.starts_at), _utc(meeting.ends_at)) != (starts_at, ends_at)
        if moved:
            await self._check_slot(meeting.company_id, starts_at, ends_at, except_id=meeting.id)
            # The candidate agreed to (or refused) another time.
            meeting.status = MeetingStatus.PENDING
        vacancy_title = await self._own_vacancy_title(user, data.vacancy_id)

        meeting.title = data.title.strip()
        meeting.starts_at = starts_at
        meeting.ends_at = ends_at
        meeting.vacancy_id = data.vacancy_id
        meeting.location = _clean(data.location)
        meeting.note = _clean(data.note)
        profile = await self._candidates.get(meeting.candidate_id)
        if moved and profile is not None:
            await announce_meeting(
                self._notifications,
                user_id=profile.user_id,
                meeting_id=meeting.id,
                company_name=company_name,
                title=meeting.title,
                starts_at=starts_at,
            )
        return _event(meeting, company_name, profile.display_name if profile else "", vacancy_title)

    async def cancel(self, user: User, meeting_id: uuid.UUID) -> None:
        meeting, _ = await self._own_meeting(user, meeting_id)
        await self._meetings.delete(meeting)

    async def respond(
        self, user: User, meeting_id: uuid.UUID, *, accept: bool
    ) -> CalendarEventRead:
        """The candidate confirms or declines; the answer can be changed later."""
        profile = await self._candidates.get_by_user(user.id)
        meeting = await self._meetings.get(meeting_id)
        if profile is None or meeting is None or meeting.candidate_id != profile.id:
            raise NotFoundError("Встреча не найдена")
        meeting.status = MeetingStatus.CONFIRMED if accept else MeetingStatus.DECLINED
        company = await self._companies.get(meeting.company_id)
        vacancy_title = None
        if meeting.vacancy_id is not None:
            row = await self._vacancies.get(meeting.vacancy_id)
            vacancy_title = row[0].title if row else None
        return _event(meeting, company.name if company else "", profile.display_name, vacancy_title)

    async def _own_meeting(self, user: User, meeting_id: uuid.UUID) -> tuple[Meeting, str]:
        company = await self._companies.get_by_owner(user.id)
        meeting = await self._meetings.get(meeting_id)
        if company is None or meeting is None or meeting.company_id != company.id:
            raise NotFoundError("Встреча не найдена")
        return meeting, company.name

    async def _own_vacancy_title(self, user: User, vacancy_id: uuid.UUID | None) -> str | None:
        if vacancy_id is None:
            return None
        row = await self._vacancies.get(vacancy_id)
        if row is None or row[1].owner_id != user.id:
            raise NotFoundError("Вакансия не найдена")
        return row[0].title

    async def _check_slot(
        self,
        company_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
        *,
        except_id: uuid.UUID | None = None,
    ) -> None:
        if starts_at <= datetime.now(UTC):
            raise AppError("Нельзя назначить встречу в прошлом")
        busy = await self._meetings.company_is_busy(
            company_id, starts_at, ends_at, except_id=except_id
        )
        if busy:
            raise ConflictError("На это время у вас уже назначена другая встреча")


def _clean(value: str | None) -> str | None:
    return (value or "").strip() or None
