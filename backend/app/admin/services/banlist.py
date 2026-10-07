"""Banned companies, emails and email domains, with the history of who blocked and unblocked."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.admin.audit import AuditLog
from app.admin.models import AdminBanEntry
from app.admin.schemas import BanCreate, BanRead
from app.core.errors import ConflictError, NotFoundError
from app.models import Company, User
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
        return Page[BanRead].build(
            [_read(*row) for row in rows], total=total or 0, page=page, per_page=per_page
        )

    async def export_rows(self, *, search: str | None, active: bool | None) -> list[BanRead]:
        rows = (
            await self._session.execute(
                self._select()
                .where(*_conditions(search, active))
                .order_by(AdminBanEntry.created_at.desc(), AdminBanEntry.id)
            )
        ).all()
        return [_read(*row) for row in rows]

    async def read(self, ban_id: uuid.UUID) -> BanRead:
        row = (
            await self._session.execute(self._select().where(AdminBanEntry.id == ban_id))
        ).first()
        if row is None:
            raise NotFoundError("Запись банлиста не найдена")
        return _read(*row)

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
        entry.is_active = False
        entry.unbanned_at = datetime.now(UTC)
        entry.unbanned_by = actor.id
        entry.unban_reason = reason
        await self._session.flush()
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


def _read(entry: AdminBanEntry, created_by: str | None, unbanned_by: str | None) -> BanRead:
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
    )
