import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import AtsSyncKind, ScreeningDecision, ScreeningJobStatus


class AtsConnection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One employer company linked to one ATS provider, and how far polling has walked."""

    __tablename__ = "ats_connections"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), unique=True
    )
    provider: Mapped[str] = mapped_column(String(32))
    cursor: Mapped[str | None] = mapped_column(String(200))


class AtsJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ats_jobs"
    __table_args__ = (UniqueConstraint("connection_id", "external_id"),)

    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ats_connections.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(200))
    required_skills: Mapped[list[str]] = mapped_column(JSON)
    salary_from: Mapped[int | None] = mapped_column(Integer)
    salary_to: Mapped[int | None] = mapped_column(Integer)
    city: Mapped[str | None] = mapped_column(String(100))


class AtsCandidate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A person who applied in an external ATS. This is not a platform user."""

    __tablename__ = "ats_candidates"
    __table_args__ = (UniqueConstraint("connection_id", "external_id"),)

    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ats_connections.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(200))
    skills: Mapped[list[str]] = mapped_column(JSON)
    experience_years: Mapped[int | None] = mapped_column(Integer)
    city: Mapped[str | None] = mapped_column(String(100))
    salary_expectation: Mapped[int | None] = mapped_column(Integer)
    resume_text: Mapped[str | None] = mapped_column(Text)


class AtsApplication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ats_applications"
    __table_args__ = (UniqueConstraint("connection_id", "external_id"),)

    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ats_connections.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ats_jobs.id", ondelete="CASCADE"))
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ats_candidates.id", ondelete="CASCADE")
    )
    external_id: Mapped[str] = mapped_column(String(128))

    job: Mapped[AtsJob] = relationship()
    candidate: Mapped[AtsCandidate] = relationship()


class AtsRawEvent(UUIDPrimaryKeyMixin, Base):
    """The provider payload, kept so a repeated poll can be recognised and inspected."""

    __tablename__ = "ats_raw_events"
    __table_args__ = (UniqueConstraint("connection_id", "provider", "external_event_id"),)

    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ats_connections.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(32))
    external_event_id: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict[str, object]] = mapped_column(JSON)
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ats_applications.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ScreeningJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One queue row per external application. A second poll does not insert another."""

    __tablename__ = "screening_jobs"

    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ats_applications.id", ondelete="CASCADE"), unique=True
    )
    status: Mapped[ScreeningJobStatus] = mapped_column(str_enum(ScreeningJobStatus), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)


class ScreeningResult(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "screening_results"

    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ats_applications.id", ondelete="CASCADE"), index=True
    )
    score: Mapped[int] = mapped_column(Integer)
    decision: Mapped[ScreeningDecision] = mapped_column(str_enum(ScreeningDecision))
    reasons: Mapped[list[str]] = mapped_column(JSON)
    matched_skills: Mapped[list[str]] = mapped_column(JSON)
    missing_skills: Mapped[list[str]] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AtsSyncLog(UUIDPrimaryKeyMixin, Base):
    """A tag, note or score this platform wrote back to the ATS."""

    __tablename__ = "ats_sync_log"

    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ats_applications.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[AtsSyncKind] = mapped_column(str_enum(AtsSyncKind))
    value: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
