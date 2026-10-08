import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    LargeBinary,
    String,
    Text,
    Uuid,
    column,
    select,
    table,
)
from sqlalchemy.orm import Mapped, column_property, deferred, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import AssessmentStatus, FspSync, Grade, JobStatus
from app.models.fsp_achievement import FspAchievement, FspSportTitle

_users = table("users", column("id", Uuid), column("last_active_at", DateTime(timezone=True)))


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
    # The owner's last sign-in: recruiters filter by «активен за 30 дней».
    last_active_at: Mapped[datetime | None] = column_property(
        select(_users.c.last_active_at).where(_users.c.id == user_id).scalar_subquery()
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

    # Participant id from the FSP ID (Keycloak) token, see `app.integrations.fsp`.
    # Null = no FSP history.
    fsp_member_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    # Load explicitly (selectinload); deletes rely on ON DELETE CASCADE.
    fsp_achievements: Mapped[list[FspAchievement]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by=(FspAchievement.year.desc(), FspAchievement.external_id),
        lazy="raise",
    )
    fsp_titles: Mapped[list[FspSportTitle]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by=(FspSportTitle.awarded_year.desc(), FspSportTitle.external_id),
        lazy="raise",
    )
    fsp_linked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Last successful import from the registry.
    fsp_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Why the last import failed; cleared by the next successful one. The link itself stays.
    fsp_sync_error: Mapped[str | None] = mapped_column(String(300))

    # Shown to an employer only after the candidate accepted an invitation or applied (ТЗ 2.2).
    phone: Mapped[str | None] = mapped_column(String(32))
    telegram: Mapped[str | None] = mapped_column(String(64))

    # Mirrors `job_status != not_looking`; search filters by this column.
    is_visible_to_employers: Mapped[bool] = mapped_column(default=True)
    job_status: Mapped[JobStatus] = mapped_column(
        str_enum(JobStatus), default=JobStatus.OPEN, server_default=JobStatus.OPEN.value
    )
    employment_types: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Never shown to employers: only the «до 18» mark derived from it.
    birth_date: Mapped[date | None] = mapped_column(Date)
    # Items: {company, position, start: "YYYY-MM", end: "YYYY-MM" | null, stack: [..]}.
    experience_entries: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    no_experience: Mapped[bool] = mapped_column(default=False)
    # Items: {institution, specialty, year}.
    education: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    github_url: Mapped[str | None] = mapped_column(String(300))
    # Separate from the personal-data consent given at sign-up.
    profile_display_consent: Mapped[bool] = mapped_column(default=False)
    fsp_sync: Mapped[FspSync | None] = mapped_column(str_enum(FspSync))

    # Resumes besides the priority one stored in the columns above. The priority resume is what
    # search and the vacancy feed rank first; these stay visible on the card.
    additional_resumes: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    # Deferred: list and search queries must not pull the image bytes.
    photo: Mapped[bytes | None] = deferred(mapped_column(LargeBinary))
    photo_type: Mapped[str | None] = mapped_column(String(32))
