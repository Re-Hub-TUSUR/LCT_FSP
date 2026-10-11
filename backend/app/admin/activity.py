"""Append-only log of employer actions and the rules that flag a company.

Nothing here restricts the company. A fired rule puts it on «Работодатели под подозрением»;
the admin decides what to do.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dictionaries import DEFAULTS
from app.admin.enums import EmployerCaseStatus
from app.admin.models import ActivityEvent, AdminEmployerCase, AdminEmployerSignal
from app.admin.services.parameters import ParameterService
from app.models import Company, User

KIND_REACTION = "candidate_reaction_change"
KIND_REQUISITES = "requisites_change"
KIND_MEETING_CREATE = "meeting_create"
KIND_MEETING_CANCEL = "meeting_cancel"
KIND_CHAT = "chat_attachment"
KIND_JUNK = "junk_vacancy"
KIND_INDUSTRY = "invalid_industry"

# Counts are admin parameters. The windows stay here: they are part of the rule, not a knob.
_TEN_MINUTES = timedelta(minutes=10)
_HOUR = timedelta(hours=1)
_DAY = timedelta(hours=24)


@dataclass(frozen=True, slots=True)
class _Rule:
    code: str
    kind: str
    parameter: str
    window: timedelta
    per_subject: bool = False


RULES: tuple[_Rule, ...] = (
    _Rule("reaction_flapping", KIND_REACTION, "reaction_flap_min", _TEN_MINUTES, per_subject=True),
    _Rule("requisites_churn", KIND_REQUISITES, "requisites_churn_min", _DAY),
    _Rule("junk_vacancies", KIND_JUNK, "junk_vacancy_min", _DAY),
    _Rule("meeting_churn", KIND_MEETING_CANCEL, "meeting_cancel_min", _DAY),
    _Rule("chat_media_spam", KIND_CHAT, "chat_media_min", _HOUR),
    _Rule("invalid_industry", KIND_INDUSTRY, "invalid_industry_min", _DAY),
)
_BY_KIND = {rule.kind: rule for rule in RULES}

# A stronger decision stays. A closed one opens again when the same abuse continues.
_REFLAG = frozenset({EmployerCaseStatus.CLEARED, EmployerCaseStatus.WARNED})


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class ActivityRecorder:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        kind: str,
        user: User,
        company: Company | None,
        subject: uuid.UUID | None = None,
    ) -> None:
        """Store the action, then flag the company when its rule's count is reached."""
        if company is None:
            return
        now = datetime.now(UTC)
        self._session.add(
            ActivityEvent(
                user_id=user.id,
                company_id=company.id,
                kind=kind,
                subject_id=subject,
                created_at=now,
            )
        )
        await self._session.flush()
        rule = _BY_KIND.get(kind)
        if rule is None:
            return
        count = await self._count(company.id, rule, subject, now)
        values = await ParameterService(self._session).values()
        threshold = int(values.get(rule.parameter, DEFAULTS[rule.parameter]))
        if count < threshold:
            return
        await self._upsert_signal(company.id, rule.code, count, now)
        await self._flag(company.id)

    async def _count(
        self, company_id: uuid.UUID, rule: _Rule, subject: uuid.UUID | None, now: datetime
    ) -> int:
        since = now - rule.window
        conditions = [
            ActivityEvent.company_id == company_id,
            ActivityEvent.kind == rule.kind,
            ActivityEvent.created_at >= since,
        ]
        if rule.per_subject:
            conditions.append(ActivityEvent.subject_id == subject)
        total = await self._session.scalar(
            select(func.count()).select_from(ActivityEvent).where(*conditions)
        )
        return int(total or 0)

    async def _upsert_signal(
        self, company_id: uuid.UUID, code: str, hits: int, now: datetime
    ) -> None:
        signal = await self._session.get(AdminEmployerSignal, (company_id, code))
        if signal is None:
            self._session.add(
                AdminEmployerSignal(
                    company_id=company_id, code=code, hits=hits, first_at=now, last_at=now
                )
            )
            return
        signal.hits = hits
        signal.last_at = now

    async def _flag(self, company_id: uuid.UUID) -> None:
        case = await self._session.get(AdminEmployerCase, company_id)
        if case is None:
            self._session.add(
                AdminEmployerCase(company_id=company_id, status=EmployerCaseStatus.FLAGGED)
            )
            return
        if case.status in _REFLAG:
            case.status = EmployerCaseStatus.FLAGGED
            case.invite_limit = None


def _blank_company_row(
    company: Company, codes: list[str], case: AdminEmployerCase
) -> dict[str, Any]:
    return {
        "companyId": str(company.id),
        "name": company.name,
        "signals": codes,
        "invitesTotal": 0,
        "invitesMaxPerDay": 0,
        "invitesMedianPerDay": None,
        "inbound": 0,
        "answered": 0,
        "responseShare": None,
        "fakeVacancyShare": None,
        "complaints": None,
        "caseStatus": case.status.value,
        "inviteLimit": case.invite_limit,
    }


async def merge_employer_rows(
    session: AsyncSession, snapshot_companies: list[dict[str, Any]] | None
) -> list[dict[str, Any]]:
    """Snapshot rows plus companies flagged live, so the list does not wait for a recount."""
    signals = (await session.scalars(select(AdminEmployerSignal))).all()
    by_company: dict[uuid.UUID, list[str]] = {}
    for signal in signals:
        by_company.setdefault(signal.company_id, []).append(signal.code)
    case_rows = (await session.scalars(select(AdminEmployerCase))).all()
    cases = {case.company_id: case for case in case_rows}
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in snapshot_companies or []:
        company_id = uuid.UUID(row["companyId"])
        codes = list(row["signals"])
        for code in by_company.get(company_id, []):
            if code not in codes:
                codes.append(code)
        case = cases.get(company_id)
        status = case.status.value if case else ("flagged" if codes else None)
        rows.append(
            {
                **row,
                "signals": codes,
                "caseStatus": status,
                "inviteLimit": case.invite_limit if case else None,
            }
        )
        seen.add(row["companyId"])
    missing = [
        company_id
        for company_id, case in cases.items()
        if case.status == EmployerCaseStatus.FLAGGED and str(company_id) not in seen
    ]
    if not missing:
        return rows
    companies = (await session.scalars(select(Company).where(Company.id.in_(missing)))).all()
    rows.extend(
        _blank_company_row(company, by_company.get(company.id, []), cases[company.id])
        for company in companies
    )
    return rows
