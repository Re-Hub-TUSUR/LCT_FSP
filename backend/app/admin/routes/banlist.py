import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.admin.audit import AuditLog
from app.admin.csv_export import csv_response
from app.admin.dependencies import BanlistDep
from app.admin.schemas import AuditEntryRead, BanCreate, BanRead, Reason
from app.admin.services.employers import audit_read
from app.dependencies.auth import AdminUser
from app.dependencies.common import SessionDep
from app.schemas.common import Page

router = APIRouter(prefix="/banlist")

PER_PAGE = 50
Search = Annotated[str | None, Query(max_length=200, description="Компания, ИНН, email, домен")]


@router.get("", summary="Banlist with search, 50 per page")
async def list_bans(
    _: AdminUser,
    service: BanlistDep,
    page: Annotated[int, Query(ge=1)] = 1,
    q: Search = None,
    active: bool | None = None,
) -> Page[BanRead]:
    return await service.page(search=q, active=active, page=page, per_page=PER_PAGE)


@router.get("/export.csv", summary="The filtered banlist as CSV")
async def export_bans(
    _: AdminUser, service: BanlistDep, q: Search = None, active: bool | None = None
) -> Response:
    rows = await service.export_rows(search=q, active=active)
    return csv_response(
        "banlist.csv",
        [
            "Компания",
            "ИНН",
            "Email",
            "Домен",
            "Причина",
            "Действует",
            "Дата",
            "Кто заблокировал",
            "Разблокирован",
            "Кто разблокировал",
            "Причина разблокировки",
        ],
        (
            [
                row.company_name,
                row.inn,
                row.email,
                row.email_domain,
                row.reason,
                row.is_active,
                row.created_at.isoformat(),
                row.created_by_email,
                row.unbanned_at.isoformat() if row.unbanned_at else None,
                row.unbanned_by_email,
                row.unban_reason,
            ]
            for row in rows
        ),
    )


@router.post("", status_code=status.HTTP_201_CREATED, summary="Block a company, email or domain")
async def add_ban(user: AdminUser, data: BanCreate, service: BanlistDep) -> BanRead:
    return await service.add(user, data)


@router.post("/{ban_id}/unban", summary="Unblock (a reason is required)")
async def unban(ban_id: uuid.UUID, user: AdminUser, data: Reason, service: BanlistDep) -> BanRead:
    return await service.unban(user, ban_id, data.reason)


@router.get("/{ban_id}/history", summary="Who blocked and unblocked, when and why")
async def ban_history(ban_id: uuid.UUID, _: AdminUser, session: SessionDep) -> list[AuditEntryRead]:
    entries, _total = await AuditLog(session).page(
        entity="banlist", entity_id=str(ban_id), limit=100, offset=0
    )
    return [audit_read(entry, email) for entry, email in entries]
