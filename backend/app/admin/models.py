"""Tables of the admin panel. They only reference existing tables, never change them."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.admin.enums import EmployerCaseStatus, TaskStatus, VerificationStatus
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum


def _now_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AdminSnapshot(UUIDPrimaryKeyMixin, Base):
    """Result of one analytics calculation an admin asked for. Pages show the latest one."""

    __tablename__ = "admin_snapshots"
    __table_args__ = (
        Index("ix_admin_snapshots_block_filters", "block", "filters_key", "computed_at"),
    )

    block: Mapped[str] = mapped_column(String(64))
    # Canonical JSON of the filters: the same filters always give the same key.
    filters_key: Mapped[str] = mapped_column(String(255))
    filters: Mapped[dict[str, Any]] = mapped_column(JSON)
    result: Mapped[dict[str, Any]] = mapped_column(JSON)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int] = mapped_column(Integer)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class AdminTaskMeta(TimestampMixin, Base):
    """What the admin panel adds to a bank task: workflow status, grade, variables, time limit.

    A task without a row here is read as `active` / `draft` by its `is_active` flag.
    """

    __tablename__ = "admin_task_meta"

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessment_tasks.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[TaskStatus] = mapped_column(str_enum(TaskStatus), index=True)
    # Code of the 11-level admin grade scale (see `app.admin.dictionaries.GRADES`).
    grade: Mapped[str | None] = mapped_column(String(16), index=True)
    # [{"name": "n", "min": 1, "max": 100, "step": 1}]: placeholders `{n}` in the statement.
    variables: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    time_limit_minutes: Mapped[int | None]


class AdminAuditLog(UUIDPrimaryKeyMixin, Base):
    """Who changed what and when: tasks, parameters, dictionaries, companies, the banlist."""

    __tablename__ = "admin_audit_log"
    __table_args__ = (Index("ix_admin_audit_log_entity", "entity", "entity_id", "created_at"),)

    entity: Mapped[str] = mapped_column(String(32))
    entity_id: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(32))
    # {"field": [old, new]} for edits, free-form details for actions.
    changes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    reason: Mapped[str | None] = mapped_column(Text)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = _now_column()


class AdminParameter(Base):
    """A platform parameter changed from its default. Missing keys mean the default."""

    __tablename__ = "admin_parameters"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = _now_column()
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class AdminSpecialization(TimestampMixin, Base):
    __tablename__ = "admin_specializations"

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(200))
    is_archived: Mapped[bool] = mapped_column(default=False)
    sort_order: Mapped[int] = mapped_column(default=0)


class AdminSkill(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "admin_skills"
    __table_args__ = (UniqueConstraint("specialization_code", "name"),)

    specialization_code: Mapped[str] = mapped_column(
        ForeignKey("admin_specializations.code", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(64))
    is_archived: Mapped[bool] = mapped_column(default=False)


class AdminEmployerCase(TimestampMixin, Base):
    """The last decision on a suspicious company and the restriction it carries."""

    __tablename__ = "admin_employer_cases"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[EmployerCaseStatus] = mapped_column(str_enum(EmployerCaseStatus), index=True)
    # Lowered daily invitation limit while the company is restricted.
    invite_limit: Mapped[int | None]
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class AdminBanEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A blocked company, email or email domain. Unblocking keeps the row for history."""

    __tablename__ = "admin_banlist"

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), index=True
    )
    company_name: Mapped[str | None] = mapped_column(String(200))
    inn: Mapped[str | None] = mapped_column(String(12), index=True)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    email_domain: Mapped[str | None] = mapped_column(String(255), index=True)
    reason: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    unbanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    unbanned_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    unban_reason: Mapped[str | None] = mapped_column(Text)


class CompanyVerification(TimestampMixin, Base):
    """Whether an admin confirmed, from the uploaded documents, that the company is real."""

    __tablename__ = "company_verifications"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[VerificationStatus] = mapped_column(str_enum(VerificationStatus), index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    decision_reason: Mapped[str | None] = mapped_column(Text)


class CompanyDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A PDF the company uploaded for the check. The bytes live in `UPLOAD_DIR`."""

    __tablename__ = "company_verification_documents"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    uploader_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    filename: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(String(500))
