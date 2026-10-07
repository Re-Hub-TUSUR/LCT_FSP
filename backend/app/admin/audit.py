"""Journal of admin actions: every change of a task, parameter, dictionary, company or ban."""

import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import AdminAuditLog
from app.models import User


def diff(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, list[Any]]:
    """{field: [old, new]} of the fields that changed."""
    return {
        key: [before.get(key), after.get(key)]
        for key in sorted(set(before) | set(after))
        if before.get(key) != after.get(key)
    }


class AuditLog:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        actor: User,
        entity: str,
        entity_id: str | uuid.UUID,
        action: str,
        changes: dict[str, Any] | None = None,
        *,
        reason: str | None = None,
    ) -> AdminAuditLog:
        entry = AdminAuditLog(
            entity=entity,
            entity_id=str(entity_id),
            action=action,
            changes=changes or {},
            reason=reason,
            actor_id=actor.id,
            # The clock of the app, not of the transaction: several entries of one request
            # keep their order.
            created_at=datetime.now(UTC),
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def page(
        self,
        *,
        entity: str | None,
        entity_id: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[tuple[AdminAuditLog, str | None]], int]:
        """Newest first, with the email of who did it."""
        conditions = []
        if entity:
            conditions.append(AdminAuditLog.entity == entity)
        if entity_id:
            conditions.append(AdminAuditLog.entity_id == entity_id)
        total = await self._session.scalar(
            select(func.count()).select_from(AdminAuditLog).where(*conditions)
        )
        rows = (
            await self._session.execute(
                select(AdminAuditLog, User.email)
                .outerjoin(User, User.id == AdminAuditLog.actor_id)
                .where(*conditions)
                .order_by(AdminAuditLog.created_at.desc(), AdminAuditLog.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
        return [(entry, email) for entry, email in rows], total or 0
