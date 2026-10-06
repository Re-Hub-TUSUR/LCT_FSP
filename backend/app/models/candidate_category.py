import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import Grade


class CandidateCategory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A grade the candidate confirmed by test in one specialization.

    A candidate may hold several; the one chosen as primary is mirrored into the profile
    (`specialization`, `grade`, `assessment_score`), which is what search and feeds read.
    """

    __tablename__ = "candidate_categories"
    __table_args__ = (
        UniqueConstraint("candidate_id", "specialization"),
        CheckConstraint("score >= 0 AND score <= 100", name="score_range"),
    )

    # The unique (candidate_id, specialization) index also serves lookups by candidate.
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE")
    )
    specialization: Mapped[str] = mapped_column(String(64))
    grade: Mapped[Grade] = mapped_column(str_enum(Grade))
    score: Mapped[float]
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Until then the grade of this specialization cannot be re-tested.
    change_allowed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Set when the confirming test was passed well: a test for this grade may start at once,
    # without waiting for `change_allowed_at`.
    recommended_grade: Mapped[Grade | None] = mapped_column(str_enum(Grade))
