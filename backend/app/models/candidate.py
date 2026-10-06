import uuid
from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import AssessmentStatus, Grade
from app.models.fsp_achievement import FspAchievement


class CandidateProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Candidate profile. The category (specialization + grade) is set by assessment only."""

    __tablename__ = "candidate_profiles"
    __table_args__ = (
        CheckConstraint(
            "assessment_score >= 0 AND assessment_score <= 100", name="assessment_score_range"
        ),
        CheckConstraint("salary_expectation > 0", name="salary_expectation_positive"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    display_name: Mapped[str] = mapped_column(String(200))
    headline: Mapped[str | None] = mapped_column(String(300))
    about: Mapped[str | None] = mapped_column(Text)
    stack: Mapped[list[str]] = mapped_column(JSON, default=list)
    soft_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    experience_years: Mapped[int | None]
    # CEFR level: A1 … C2.
    english_level: Mapped[str | None] = mapped_column(String(2))

    # Job preferences used to rank the vacancy feed.
    city: Mapped[str | None] = mapped_column(String(100))
    relocation_ready: Mapped[bool] = mapped_column(default=False)
    work_formats: Mapped[list[str]] = mapped_column(JSON, default=list)
    # Desired monthly salary, RUB.
    salary_expectation: Mapped[int | None]

    specialization: Mapped[str | None] = mapped_column(String(64), index=True)
    grade: Mapped[Grade | None] = mapped_column(
        str_enum(Grade),
        index=True,
    )
    # 0–100 for the current grade. Null = the test was skipped and the grade is self-declared.
    assessment_score: Mapped[float | None]
    grade_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Passed = the category above is confirmed; failed = tried and has no confirmed category.
    assessment_status: Mapped[AssessmentStatus] = mapped_column(
        str_enum(AssessmentStatus),
        default=AssessmentStatus.NOT_TAKEN,
        server_default=AssessmentStatus.NOT_TAKEN.value,
    )

    # Link to the FSP participant registry (future Keycloak-based FSP ID). Null = no FSP history.
    fsp_member_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    # Load explicitly (selectinload); deletes rely on ON DELETE CASCADE.
    fsp_achievements: Mapped[list[FspAchievement]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by=FspAchievement.year.desc(),
        lazy="raise",
    )

    # Shown to an employer only after the candidate accepted an invitation or applied (ТЗ 2.2).
    phone: Mapped[str | None] = mapped_column(String(32))
    telegram: Mapped[str | None] = mapped_column(String(64))

    is_visible_to_employers: Mapped[bool] = mapped_column(default=True)
