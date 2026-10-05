import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import Grade


class CandidateProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Candidate profile. The category (specialization + grade) is set by assessment only."""

    __tablename__ = "candidate_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    display_name: Mapped[str] = mapped_column(String(200))
    headline: Mapped[str | None] = mapped_column(String(300))
    about: Mapped[str | None] = mapped_column(Text)
    stack: Mapped[list[str]] = mapped_column(JSON, default=list)
    experience_years: Mapped[int | None]

    specialization: Mapped[str | None] = mapped_column(String(64), index=True)
    grade: Mapped[Grade | None] = mapped_column(
        str_enum(Grade),
        index=True,
    )
    grade_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Link to the FSP participant registry (future Keycloak-based FSP ID). Null = no FSP history.
    fsp_member_id: Mapped[str | None] = mapped_column(String(64), unique=True)

    is_visible_to_employers: Mapped[bool] = mapped_column(default=True)
