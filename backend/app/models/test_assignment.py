import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import AssignmentStatus


class TestAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A company's own test sent to a candidate after a match («тестовое»).

    The attempt that answers it points back here (`assessment_attempts.assignment_id`).
    """

    __tablename__ = "test_assignments"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True
    )
    test_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assessment_tests.id", ondelete="SET NULL")
    )
    # The position the test is about, if any.
    vacancy_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vacancies.id", ondelete="SET NULL")
    )
    # Copied from the template, so the lists read the same after the template changes or goes.
    title: Mapped[str] = mapped_column(String(200))
    duration_minutes: Mapped[int]
    tasks_count: Mapped[int]
    message: Mapped[str | None] = mapped_column(Text)
    # The candidate may start until then.
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[AssignmentStatus] = mapped_column(
        str_enum(AssignmentStatus), default=AssignmentStatus.SENT, index=True
    )
