import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import InvitationStatus


class Invitation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Employer-initiated contact — the central mechanic of the platform.

    Not necessarily tied to a published vacancy; salary range is mandatory (ТЗ 2.2, items 1–3).
    """

    __tablename__ = "invitations"
    __table_args__ = (
        CheckConstraint("salary_from > 0 AND salary_from <= salary_to", name="salary_range"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True
    )
    vacancy_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vacancies.id", ondelete="SET NULL")
    )
    message: Mapped[str] = mapped_column(Text)
    salary_from: Mapped[int]
    salary_to: Mapped[int]
    contact_method: Mapped[str] = mapped_column(String(200))
    status: Mapped[InvitationStatus] = mapped_column(
        str_enum(InvitationStatus),
        default=InvitationStatus.SENT,
    )
