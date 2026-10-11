"""Banned companies, emails and email domains, with the history of who blocked and unblocked."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import ColumnElement, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.admin.audit import AuditLog
from app.admin.models import AdminBanEntry
from app.admin.schemas import BanAccountRead, BanCreate, BanRead
from app.core.config import Settings
from app.core.errors import AccountBannedError, ConflictError, NotFoundError
from app.models import Company, RefreshToken, User
from app.schemas.common import Page


def _conditions(search: str | None, active: bool | None) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if active is not None:
        conditions.append(AdminBanEntry.is_active.is_(active))
    if search:
        pattern = f"%{search.strip()}%"
        conditions.append(
            or_(
                AdminBanEntry.company_name.ilike(pattern),
                AdminBanEntry.inn.ilike(pattern),
                AdminBanEntry.email.ilike(pattern),
                AdminBanEntry.email_domain.ilike(pattern),
                AdminBanEntry.reason.ilike(pattern),
            )
        )
    return conditions


class BanlistService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditLog(session)

    def _select(self) -> Any:
        creator = aliased(User)
        remover = aliased(User)
        return (
            select(AdminBanEntry, creator.email, remover.email)
            .outerjoin(creator, creator.id == AdminBanEntry.created_by)
            .outerjoin(remover, remover.id == AdminBanEntry.unbanned_by)
        )

    async def page(
        self, *, search: str | None, active: bool | None, page: int, per_page: int
    ) -> Page[BanRead]:
        conditions = _conditions(search, active)
        total = await self._session.scalar(
            select(func.count()).select_from(AdminBanEntry).where(*conditions)
        )
        rows = (
            await self._session.execute(
                self._select()
                .where(*conditions)
                .order_by(AdminBanEntry.created_at.desc(), AdminBanEntry.id)
                .limit(per_page)
                .offset((page - 1) * per_page)
            )
        ).all()
        items = [await _present(self._session, *row) for row in rows]
        return Page[BanRead].build(
            items, total=total or 0, page=page, per_page=per_page
        )

    async def export_rows(self, *, search: str | None, active: bool | None) -> list[BanRead]:
        rows = (
            await self._session.execute(
                self._select()
                .where(*_conditions(search, active))
                .order_by(AdminBanEntry.created_at.desc(), AdminBanEntry.id)
            )
        ).all()
        return [await _present(self._session, *row) for row in rows]

    async def read(self, ban_id: uuid.UUID) -> BanRead:
        row = (
            await self._session.execute(self._select().where(AdminBanEntry.id == ban_id))
        ).first()
        if row is None:
            raise NotFoundError("Запись банлиста не найдена")
        return await _present(self._session, *row)

    async def add(self, actor: User, data: BanCreate) -> BanRead:
        name = data.company_name
        if data.company_id is not None:
            company = await self._session.get(Company, data.company_id)
            if company is None:
                raise NotFoundError("Компания не найдена")
            name = name or company.name
        entry = AdminBanEntry(
            company_id=data.company_id,
            company_name=name,
            inn=data.inn,
            email=data.email,
            email_domain=data.email_domain,
            reason=data.reason,
            is_active=True,
            created_by=actor.id,
        )
        self._session.add(entry)
        await self._session.flush()
        await self._revoke([user.id for user in await matched_users(self._session, entry)])
        await self._audit.record(
            actor,
            "banlist",
            entry.id,
            "ban",
            {
                key: [None, value]
                for key, value in {
                    "companyName": name,
                    "inn": data.inn,
                    "email": data.email,
                    "emailDomain": data.email_domain,
                }.items()
                if value
            },
            reason=data.reason,
        )
        return await self.read(entry.id)

    async def unban(self, actor: User, ban_id: uuid.UUID, reason: str) -> BanRead:
        entry = await self._session.get(AdminBanEntry, ban_id)
        if entry is None:
            raise NotFoundError("Запись банлиста не найдена")
        if not entry.is_active:
            raise ConflictError("Запись уже разблокирована")
        affected = await matched_users(self._session, entry)
        entry.is_active = False
        entry.unbanned_at = datetime.now(UTC)
        entry.unbanned_by = actor.id
        entry.unban_reason = reason
        await self._session.flush()
        for user in affected:
            if await active_ban_for(self._session, user) is None:
                user.is_active = True
        await self._audit.record(
            actor, "banlist", entry.id, "unban", {"isActive": [True, False]}, reason=reason
        )
        return await self.read(entry.id)

    async def active_for_company(self, company_id: uuid.UUID) -> bool:
        found = await self._session.scalar(
            select(AdminBanEntry.id)
            .where(AdminBanEntry.company_id == company_id, AdminBanEntry.is_active.is_(True))
            .limit(1)
        )
        return found is not None

    async def _revoke(self, user_ids: list[uuid.UUID]) -> None:
        if not user_ids:
            return
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id.in_(user_ids), RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
            .execution_options(synchronize_session=False)
        )


def ban_details(entry: AdminBanEntry, settings: Settings) -> dict[str, str]:
    return {"reason": entry.reason, "supportEmail": settings.support_email}


def raise_if_banned(entry: AdminBanEntry | None, settings: Settings) -> None:
    if entry is not None:
        raise AccountBannedError(details=ban_details(entry, settings))


async def active_ban_for_email(session: AsyncSession, email: str) -> AdminBanEntry | None:
    """An active row for this exact address or its domain. An empty domain matches nobody."""
    normalized = email.strip().lower()
    domain = normalized.partition("@")[2]
    clauses = [func.lower(AdminBanEntry.email) == normalized]
    if domain:
        clauses.append(func.lower(AdminBanEntry.email_domain) == domain)
    return await session.scalar(
        select(AdminBanEntry)
        .where(AdminBanEntry.is_active.is_(True), or_(*clauses))
        .order_by(AdminBanEntry.created_at.desc())
        .limit(1)
    )


async def active_ban_for(session: AsyncSession, user: User) -> AdminBanEntry | None:
    """Email, domain, the company this person owns, or that company's INN."""
    found = await active_ban_for_email(session, user.email)
    if found is not None:
        return found
    company = await session.scalar(select(Company).where(Company.owner_id == user.id))
    if company is None:
        return None
    clauses = [AdminBanEntry.company_id == company.id]
    if company.inn:
        clauses.append(AdminBanEntry.inn == company.inn)
    return await session.scalar(
        select(AdminBanEntry)
        .where(AdminBanEntry.is_active.is_(True), or_(*clauses))
        .order_by(AdminBanEntry.created_at.desc())
        .limit(1)
    )


async def matched_users(session: AsyncSession, entry: AdminBanEntry) -> list[User]:
    clauses: list[ColumnElement[bool]] = []
    if entry.email:
        clauses.append(func.lower(User.email) == entry.email.strip().lower())
    domain = (entry.email_domain or "").strip().lower().removeprefix("@")
    if domain:
        clauses.append(func.lower(User.email).endswith(f"@{domain}"))
    company_filters: list[ColumnElement[bool]] = []
    if entry.company_id is not None:
        company_filters.append(Company.id == entry.company_id)
    if entry.inn:
        company_filters.append(Company.inn == entry.inn)
    if company_filters:
        owners = list(
            await session.scalars(select(Company.owner_id).where(or_(*company_filters)))
        )
        if owners:
            clauses.append(User.id.in_(owners))
    if not clauses:
        return []
    return list((await session.scalars(select(User).where(or_(*clauses)))).all())


async def _present(
    session: AsyncSession, entry: AdminBanEntry, created_by: str | None, unbanned_by: str | None
) -> BanRead:
    users = await matched_users(session, entry)
    return BanRead(
        id=entry.id,
        company_id=entry.company_id,
        company_name=entry.company_name,
        inn=entry.inn,
        email=entry.email,
        email_domain=entry.email_domain,
        reason=entry.reason,
        is_active=entry.is_active,
        created_at=entry.created_at,
        created_by_email=created_by,
        unbanned_at=entry.unbanned_at,
        unbanned_by_email=unbanned_by,
        unban_reason=entry.unban_reason,
        accounts=[BanAccountRead(email=user.email, role=user.role.value) for user in users],
    )
