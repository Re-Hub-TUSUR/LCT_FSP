"""Admin side of the company document check."""

import uuid
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Query, Response

from app.admin.csv_export import csv_response
from app.admin.dependencies import VerificationDep
from app.admin.enums import VerificationStatus
from app.admin.schemas import Reason, VerificationApprove, VerificationDetail, VerificationRow
from app.admin.services.verification import MEDIA_TYPES, DocumentKind, document_kind
from app.dependencies.auth import AdminUser
from app.schemas.common import Page

router = APIRouter(prefix="/verifications")

PER_PAGE = 50
STATUS_LABELS = {
    VerificationStatus.PENDING: "На проверке",
    VerificationStatus.APPROVED: "Подтверждена",
    VerificationStatus.REJECTED: "Отклонена",
}
Search = Annotated[str | None, Query(max_length=200, description="Название компании")]


def document_response(filename: str, data: bytes, kind: DocumentKind) -> Response:
    """A PDF opens in the browser's viewer, a DOCX downloads. The name is RFC 5987-encoded
    (Cyrillic)."""
    disposition = "inline" if kind == "pdf" else "attachment"
    return Response(
        content=data,
        media_type=MEDIA_TYPES[kind],
        headers={
            "Content-Disposition": (
                f"{disposition}; filename=\"document.{kind}\"; filename*=UTF-8''{quote(filename)}"
            ),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("", summary="Requests, waiting ones first")
async def list_requests(
    _: AdminUser,
    service: VerificationDep,
    page: Annotated[int, Query(ge=1)] = 1,
    request_status: Annotated[VerificationStatus | None, Query(alias="status")] = None,
    q: Search = None,
) -> Page[VerificationRow]:
    return await service.page(status=request_status, search=q, page=page, per_page=PER_PAGE)


@router.get("/pending-count", summary="How many requests wait for a decision")
async def pending_count(_: AdminUser, service: VerificationDep) -> int:
    return await service.pending_count()


@router.get("/export.csv", summary="Requests as CSV")
async def export_requests(
    _: AdminUser,
    service: VerificationDep,
    request_status: Annotated[VerificationStatus | None, Query(alias="status")] = None,
    q: Search = None,
) -> Response:
    rows = []
    page = 1
    while True:
        chunk = await service.page(status=request_status, search=q, page=page, per_page=500)
        rows.extend(chunk.items)
        if page >= chunk.pages:
            break
        page += 1
    return csv_response(
        "company-verification.csv",
        ["Компания", "Email владельца", "Статус", "Подана", "Решение", "Документов"],
        (
            [
                row.company_name,
                row.owner_email,
                STATUS_LABELS[row.status],
                row.submitted_at.isoformat(),
                row.decided_at.isoformat() if row.decided_at else None,
                row.documents,
            ]
            for row in rows
        ),
    )


@router.get("/{company_id}", summary="A request with its documents and history")
async def read_request(
    company_id: uuid.UUID, _: AdminUser, service: VerificationDep
) -> VerificationDetail:
    return await service.detail(company_id)


@router.get("/{company_id}/documents/{document_id}", summary="The document itself")
async def read_document(
    company_id: uuid.UUID, document_id: uuid.UUID, _: AdminUser, service: VerificationDep
) -> Response:
    document, data = await service.document_bytes(company_id, document_id)
    return document_response(document.filename, data, document_kind(document))


@router.post("/{company_id}/approve", summary="Confirm the company is real")
async def approve(
    company_id: uuid.UUID, user: AdminUser, data: VerificationApprove, service: VerificationDep
) -> VerificationDetail:
    return await service.decide(user, company_id, approve=True, reason=data.comment)


@router.post(
    "/{company_id}/reject", summary="Reject the request (the reason is shown to the company)"
)
async def reject(
    company_id: uuid.UUID, user: AdminUser, data: Reason, service: VerificationDep
) -> VerificationDetail:
    return await service.decide(user, company_id, approve=False, reason=data.reason)
