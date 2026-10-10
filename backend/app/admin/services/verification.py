"""A company proves its IT accreditation: it uploads the Минцифры registry extract (PDF or
DOCX), an admin approves or rejects the request.

Uploading the first document opens a request; a new upload after a rejection reopens it. An
approved company may add documents without losing its status.
"""

import io
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.admin.audit import AuditLog
from app.admin.enums import VerificationStatus
from app.admin.models import CompanyDocument, CompanyVerification
from app.admin.schemas import (
    CompanyDocumentRead,
    VerificationDetail,
    VerificationRead,
    VerificationRow,
)
from app.admin.services.employers import audit_read
from app.core.config import Settings
from app.core.errors import AppError, ConflictError, NotFoundError
from app.models import Company, User
from app.schemas.common import Page
from app.services.notifications import NotificationHub

DOCUMENT_LIMIT: Final = 10 * 1024 * 1024
MAX_DOCUMENTS: Final = 10
_PDF: Final = b"%PDF-"
_ZIP: Final = b"PK\x03\x04"
_DOCX_BODY: Final = "word/document.xml"
STORAGE_DIR: Final = "company-documents"

DocumentKind = Literal["pdf", "docx"]
MEDIA_TYPES: Final[dict[DocumentKind, str]] = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def sniff_document(data: bytes) -> DocumentKind | None:
    """The bytes decide: a PDF, or a Word file (a ZIP with the document body inside)."""
    if data.startswith(_PDF):
        return "pdf"
    if data.startswith(_ZIP):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if _DOCX_BODY in archive.namelist():
                    return "docx"
        except zipfile.BadZipFile:
            return None
    return None


def document_kind(document: CompanyDocument) -> DocumentKind:
    return "docx" if document.storage_key.endswith(".docx") else "pdf"


def _document(document: CompanyDocument) -> CompanyDocumentRead:
    return CompanyDocumentRead(
        id=document.id,
        filename=document.filename,
        size_bytes=document.size_bytes,
        uploaded_at=document.created_at,
        kind=document_kind(document),
    )


def clean_filename(name: str | None, kind: DocumentKind = "pdf") -> str:
    """Only the last path part, no control characters, the extension of the detected type."""
    base = Path((name or "").replace("\\", "/")).name
    base = "".join(char for char in base if char.isprintable() and char not in '"<>|')
    base = base.strip()[:200] or "document"
    suffix = f".{kind}"
    return base if base.lower().endswith(suffix) else f"{base}{suffix}"


class VerificationService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        notifications: NotificationHub | None = None,
    ) -> None:
        self._session = session
        self._root = Path(settings.upload_dir) / STORAGE_DIR
        self._audit = AuditLog(session)
        self._notifications = notifications

    # ── Employer ──────────────────────────────────────────────────────────────────────────

    async def mine(self, user: User) -> VerificationRead:
        company = await self._own_company(user)
        verification = await self._session.get(CompanyVerification, company.id)
        documents = await self._documents(company.id)
        return VerificationRead(
            status=verification.status if verification else None,
            submitted_at=verification.submitted_at if verification else None,
            decided_at=verification.decided_at if verification else None,
            reason=verification.decision_reason
            if verification and verification.status == VerificationStatus.REJECTED
            else None,
            documents=[_document(document) for document in documents],
        )

    async def upload(self, user: User, filename: str | None, data: bytes) -> VerificationRead:
        company = await self._own_company(user)
        if len(data) > DOCUMENT_LIMIT:
            raise AppError("Файл больше 10 МБ")
        kind = sniff_document(data)
        if kind is None:
            raise AppError("Нужна выписка в формате PDF или DOCX")
        if len(await self._documents(company.id)) >= MAX_DOCUMENTS:
            raise ConflictError(f"Можно загрузить не больше {MAX_DOCUMENTS} документов")

        storage_key = f"{company.id}/{uuid.uuid4()}.{kind}"
        self._session.add(
            CompanyDocument(
                company_id=company.id,
                uploader_id=user.id,
                filename=clean_filename(filename, kind),
                size_bytes=len(data),
                storage_key=storage_key,
            )
        )

        now = datetime.now(UTC)
        verification = await self._session.get(CompanyVerification, company.id)
        if verification is None:
            self._session.add(
                CompanyVerification(
                    company_id=company.id, status=VerificationStatus.PENDING, submitted_at=now
                )
            )
        elif verification.status == VerificationStatus.REJECTED:
            # New documents after a rejection are a new request.
            verification.status = VerificationStatus.PENDING
            verification.submitted_at = now
            verification.decided_at = None
            verification.decided_by = None
            verification.decision_reason = None
        await self._session.flush()
        # Written after the rows: a database error no longer leaves a file nobody knows of.
        path = self._root / storage_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return await self.mine(user)

    async def remove(self, user: User, document_id: uuid.UUID) -> VerificationRead:
        company = await self._own_company(user)
        document = await self._session.get(CompanyDocument, document_id)
        if document is None or document.company_id != company.id:
            raise NotFoundError("Документ не найден")
        verification = await self._session.get(CompanyVerification, company.id)
        if verification is not None and verification.status == VerificationStatus.APPROVED:
            raise ConflictError("Компания уже подтверждена: документы проверки не удаляются")
        await self._session.delete(document)
        await self._session.flush()
        (self._root / document.storage_key).unlink(missing_ok=True)
        return await self.mine(user)

    # ── Admin ─────────────────────────────────────────────────────────────────────────────

    def _conditions(
        self, status: VerificationStatus | None, search: str | None
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if status is not None:
            conditions.append(CompanyVerification.status == status)
        if search:
            conditions.append(Company.name.ilike(f"%{search.strip()}%"))
        return conditions

    async def page(
        self, *, status: VerificationStatus | None, search: str | None, page: int, per_page: int
    ) -> Page[VerificationRow]:
        conditions = self._conditions(status, search)
        documents = (
            select(func.count())
            .where(CompanyDocument.company_id == CompanyVerification.company_id)
            .scalar_subquery()
        )
        total = await self._session.scalar(
            select(func.count())
            .select_from(CompanyVerification)
            .join(Company, Company.id == CompanyVerification.company_id)
            .where(*conditions)
        )
        rows = (
            await self._session.execute(
                select(CompanyVerification, Company, User.email, documents.label("documents"))
                .join(Company, Company.id == CompanyVerification.company_id)
                .join(User, User.id == Company.owner_id)
                .where(*conditions)
                # Waiting requests first, the oldest of them on top.
                .order_by(
                    (CompanyVerification.status != VerificationStatus.PENDING),
                    CompanyVerification.submitted_at,
                    Company.id,
                )
                .limit(per_page)
                .offset((page - 1) * per_page)
            )
        ).all()
        return Page[VerificationRow].build(
            [
                VerificationRow(
                    company_id=company.id,
                    company_name=company.name,
                    owner_email=email,
                    status=verification.status,
                    submitted_at=verification.submitted_at,
                    decided_at=verification.decided_at,
                    documents=int(count or 0),
                )
                for verification, company, email, count in rows
            ],
            total=total or 0,
            page=page,
            per_page=per_page,
        )

    async def pending_count(self) -> int:
        count = await self._session.scalar(
            select(func.count())
            .select_from(CompanyVerification)
            .where(CompanyVerification.status == VerificationStatus.PENDING)
        )
        return count or 0

    async def detail(self, company_id: uuid.UUID) -> VerificationDetail:
        verification = await self._session.get(CompanyVerification, company_id)
        company = await self._session.get(Company, company_id)
        if verification is None or company is None:
            raise NotFoundError("Заявка не найдена")
        owner = await self._session.get(User, company.owner_id)
        decider = aliased(User)
        decided_by = (
            await self._session.scalar(
                select(decider.email).where(decider.id == verification.decided_by)
            )
            if verification.decided_by
            else None
        )
        documents = await self._documents(company_id)
        history, _ = await self._audit.page(
            entity="verification", entity_id=str(company_id), limit=50, offset=0
        )
        return VerificationDetail(
            company_id=company.id,
            company_name=company.name,
            owner_email=owner.email if owner else "",
            status=verification.status,
            submitted_at=verification.submitted_at,
            decided_at=verification.decided_at,
            documents=len(documents),
            industry=company.industry,
            city=company.city,
            website=company.website,
            contact_email=company.contact_email,
            decision_reason=verification.decision_reason,
            decided_by_email=decided_by,
            files=[_document(document) for document in documents],
            history=[audit_read(entry, email) for entry, email in history],
        )

    async def document_bytes(
        self, company_id: uuid.UUID, document_id: uuid.UUID
    ) -> tuple[CompanyDocument, bytes]:
        document = await self._session.get(CompanyDocument, document_id)
        if document is None or document.company_id != company_id:
            raise NotFoundError("Документ не найден")
        path = self._root / document.storage_key
        if not path.is_file():
            raise NotFoundError("Файл документа не найден в хранилище")
        return document, path.read_bytes()

    async def decide(
        self, actor: User, company_id: uuid.UUID, *, approve: bool, reason: str | None
    ) -> VerificationDetail:
        verification = await self._session.get(CompanyVerification, company_id)
        if verification is None:
            raise NotFoundError("Заявка не найдена")
        if not await self._documents(company_id):
            raise ConflictError("В заявке нет документов")
        target = VerificationStatus.APPROVED if approve else VerificationStatus.REJECTED
        before = verification.status
        verification.status = target
        verification.decided_at = datetime.now(UTC)
        verification.decided_by = actor.id
        verification.decision_reason = reason
        await self._session.flush()
        await self._audit.record(
            actor,
            "verification",
            company_id,
            "approve" if approve else "reject",
            {"status": [before.value, target.value]},
            reason=reason,
        )
        detail = await self.detail(company_id)
        await self._notify(company_id, target, reason)
        return detail

    # ── Helpers ───────────────────────────────────────────────────────────────────────────

    async def _notify(
        self, company_id: uuid.UUID, status: VerificationStatus, reason: str | None
    ) -> None:
        if self._notifications is None:
            return
        company = await self._session.get(Company, company_id)
        if company is None:
            return
        await self._notifications.publish(
            company.owner_id,
            {
                "type": "company_verification",
                "status": status.value,
                "reason": reason if status == VerificationStatus.REJECTED else None,
            },
        )

    async def _own_company(self, user: User) -> Company:
        company = await self._session.scalar(select(Company).where(Company.owner_id == user.id))
        if company is None:
            raise NotFoundError("Сначала заполните и сохраните профиль компании")
        return company

    async def _documents(self, company_id: uuid.UUID) -> list[CompanyDocument]:
        rows = await self._session.scalars(
            select(CompanyDocument)
            .where(CompanyDocument.company_id == company_id)
            .order_by(CompanyDocument.created_at, CompanyDocument.id)
        )
        return list(rows)
