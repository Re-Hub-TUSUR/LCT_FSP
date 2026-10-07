"""Decisions on suspicious companies and the card an admin decides from."""

import uuid
from typing import Any, Final

from sqlalchemy import literal_column, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.analytics.employers import company_signal_rows
from app.admin.audit import AuditLog
from app.admin.enums import EmployerCaseStatus
from app.admin.models import AdminEmployerCase, CompanyVerification
from app.admin.schemas import (
    AnalyticsFilters,
    AuditEntryRead,
    BanCreate,
    EmployerCard,
    EmployerCaseRead,
    EmployerDecision,
    EmployerOutreachRow,
    EmployerVacancyRow,
)
from app.admin.services.banlist import BanlistService
from app.admin.services.snapshots import SnapshotService, meta
from app.core.errors import NotFoundError
from app.models import (
    CandidateProfile,
    CandidateReaction,
    Company,
    Invitation,
    ReactionKind,
    TestAssignment,
    User,
    Vacancy,
)

DECISIONS: Final = {
    "clear": EmployerCaseStatus.CLEARED,
    "warn": EmployerCaseStatus.WARNED,
    "restrict": EmployerCaseStatus.RESTRICTED,
    "block": EmployerCaseStatus.BLOCKED,
}
HISTORY_LIMIT: Final = 50


def audit_read(entry: Any, email: str | None) -> AuditEntryRead:
    return AuditEntryRead(
        id=entry.id,
        entity=entry.entity,
        entity_id=entry.entity_id,
        action=entry.action,
        changes=entry.changes,
        reason=entry.reason,
        actor_email=email,
        created_at=entry.created_at,
    )


class EmployerModerationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditLog(session)
        self._banlist = BanlistService(session)

    async def cases(self, company_ids: list[uuid.UUID]) -> dict[uuid.UUID, AdminEmployerCase]:
        if not company_ids:
            return {}
        rows = await self._session.scalars(
            select(AdminEmployerCase).where(AdminEmployerCase.company_id.in_(company_ids))
        )
        return {row.company_id: row for row in rows}

    async def decide(
        self, actor: User, company_id: uuid.UUID, data: EmployerDecision
    ) -> EmployerCard:
        company = await self._company(company_id)
        case = await self._session.get(AdminEmployerCase, company_id)
        before = case.status.value if case else None
        status = DECISIONS[data.action]
        if case is None:
            case = AdminEmployerCase(company_id=company_id, status=status)
            self._session.add(case)
        case.status = status
        case.invite_limit = data.invite_limit if data.action == "restrict" else None
        case.updated_by = actor.id
        await self._session.flush()
        changes: dict[str, Any] = {"status": [before, status.value]}
        if data.action == "restrict":
            changes["inviteLimit"] = [None, data.invite_limit]
        await self._audit.record(
            actor, "company", company_id, data.action, changes, reason=data.reason
        )
        if data.action == "block" and not await self._banlist.active_for_company(company_id):
            owner = await self._session.get(User, company.owner_id)
            await self._banlist.add(
                actor,
                BanCreate(
                    company_id=company_id,
                    company_name=company.name,
                    email=owner.email if owner else None,
                    reason=data.reason,
                ),
            )
        return await self.card(company_id)

    async def card(
        self, company_id: uuid.UUID, filters: AnalyticsFilters | None = None
    ) -> EmployerCard:
        company = await self._company(company_id)
        owner = await self._session.get(User, company.owner_id)
        # Re-read: updated_at is set by the database and expires after a flush.
        case = await self._session.get(AdminEmployerCase, company_id, populate_existing=True)
        verification = await self._session.get(CompanyVerification, company_id)
        snapshot = await SnapshotService(self._session).latest(
            "employers", filters or AnalyticsFilters()
        )
        vacancies = await self._session.scalars(
            select(Vacancy)
            .where(Vacancy.company_id == company_id)
            .order_by(Vacancy.created_at.desc())
            .limit(HISTORY_LIMIT)
        )
        history, _ = await self._audit.page(
            entity="company", entity_id=str(company_id), limit=HISTORY_LIMIT, offset=0
        )
        return EmployerCard(
            company_id=company.id,
            name=company.name,
            industry=company.industry,
            city=company.city,
            website=company.website,
            contact_email=company.contact_email,
            owner_email=owner.email if owner else "",
            registered_at=company.created_at,
            case=EmployerCaseRead(
                status=case.status, invite_limit=case.invite_limit, updated_at=case.updated_at
            )
            if case
            else None,
            verification=verification.status if verification else None,
            banned=await self._banlist.active_for_company(company_id),
            signals=company_signal_rows(snapshot.result, company_id) if snapshot else None,
            snapshot=meta(snapshot) if snapshot else None,
            vacancies=[
                EmployerVacancyRow(
                    id=vacancy.id,
                    title=vacancy.title,
                    specialization=vacancy.specialization,
                    grade=vacancy.grade.value,
                    published_at=vacancy.published_at,
                    created_at=vacancy.created_at,
                )
                for vacancy in vacancies
            ],
            outreach=await self._outreach(company),
            history=[audit_read(entry, email) for entry, email in history],
        )

    async def _outreach(self, company: Company) -> list[EmployerOutreachRow]:
        """The latest ways the company reached out to candidates: likes, invitations, tests."""
        parts = union_all(
            select(
                literal_column("'like'").label("kind"),
                CandidateReaction.candidate_id.label("candidate_id"),
                literal_column("NULL").label("status"),
                CandidateReaction.created_at.label("created_at"),
            ).where(
                CandidateReaction.user_id == company.owner_id,
                CandidateReaction.kind == ReactionKind.LIKE,
            ),
            select(
                literal_column("'invitation'"),
                Invitation.candidate_id,
                Invitation.status,
                Invitation.created_at,
            ).where(Invitation.company_id == company.id),
            select(
                literal_column("'test'"),
                TestAssignment.candidate_id,
                TestAssignment.status,
                TestAssignment.created_at,
            ).where(TestAssignment.company_id == company.id),
        ).subquery()
        rows = (
            await self._session.execute(
                select(parts, CandidateProfile.display_name)
                .join(CandidateProfile, CandidateProfile.id == parts.c.candidate_id)
                .order_by(parts.c.created_at.desc())
                .limit(HISTORY_LIMIT)
            )
        ).all()
        return [
            EmployerOutreachRow(
                kind=row.kind,
                candidate_id=row.candidate_id,
                candidate_name=row.display_name,
                status=str(row.status) if row.status is not None else None,
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def _company(self, company_id: uuid.UUID) -> Company:
        company = await self._session.get(Company, company_id)
        if company is None:
            raise NotFoundError("Компания не найдена")
        return company
