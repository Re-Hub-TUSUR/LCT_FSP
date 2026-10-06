import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import MeetingStatus


class Meeting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An interview slot a company put into its own and the candidate's calendar."""

    __tablename__ = "meetings"
    __table_args__ = (CheckConstraint("starts_at < ends_at", name="time_range"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True
    )
    # The position the interview is about, if any.
    vacancy_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vacancies.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(200))
    # Always UTC.
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Video call link or office address.
    location: Mapped[str | None] = mapped_column(String(500))
    note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[MeetingStatus] = mapped_column(
        str_enum(MeetingStatus), default=MeetingStatus.PENDING
    )
