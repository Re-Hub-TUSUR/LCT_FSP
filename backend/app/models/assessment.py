import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import AttemptStatus, Grade, TaskDifficulty, TaskKind


class AssessmentTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One item of the task bank. `payload` holds the kind-specific content (see schemas)."""

    __tablename__ = "assessment_tasks"

    # Null = the platform bank (managed by admins); otherwise the employer who wrote the task.
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[TaskKind] = mapped_column(str_enum(TaskKind), index=True)
    difficulty: Mapped[TaskDifficulty] = mapped_column(str_enum(TaskDifficulty))
    # Empty list = fits any specialization.
    specializations: Mapped[list[str]] = mapped_column(JSON, default=list)
    topic: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(200))
    statement: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(default=True)


class AssessmentTest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Test template: how an attempt is composed, timed and scored."""

    __tablename__ = "assessment_tests"
    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="duration_positive"),
        CheckConstraint("pass_score >= 0 AND pass_score <= 100", name="pass_score_range"),
        CheckConstraint("quiz_weight >= 0 AND quiz_weight <= 100", name="quiz_weight_range"),
    )

    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    # Platform templates only: the grade this test confirms.
    grade: Mapped[Grade | None] = mapped_column(str_enum(Grade), index=True)
    duration_minutes: Mapped[int]
    pass_score: Mapped[int] = mapped_column(default=60)
    # Share of quiz questions in the score, percent; the rest belongs to code tasks.
    quiz_weight: Mapped[int] = mapped_column(default=40)
    composition: Mapped[dict[str, Any]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(default=True)


class AssessmentAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assessment_attempts"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True
    )
    test_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assessment_tests.id", ondelete="SET NULL")
    )
    # Copied from the template, so the history reads the same after the template changes.
    title: Mapped[str] = mapped_column(String(200))
    # Set for platform grade tests; null for an employer's own test.
    specialization: Mapped[str | None] = mapped_column(String(64))
    grade: Mapped[Grade | None] = mapped_column(str_enum(Grade))
    status: Mapped[AttemptStatus] = mapped_column(
        str_enum(AttemptStatus), default=AttemptStatus.IN_PROGRESS
    )
    score: Mapped[float | None]
    # Scoring rules are copied from the template: later edits do not change a running attempt.
    pass_score: Mapped[int]
    quiz_weight: Mapped[int]
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # The variant handed to this candidate, in display order.
    task_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    # task id → order of quiz options as shown (position → index in the bank).
    option_orders: Mapped[dict[str, list[int]]] = mapped_column(JSON, default=dict)
    # Per-topic result, filled on finish.
    breakdown: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    runs_count: Mapped[int] = mapped_column(default=0)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Signals for reviewers; they never change the score.
    paste_count: Mapped[int] = mapped_column(default=0)
    blur_count: Mapped[int] = mapped_column(default=0)


class AssessmentAnswer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assessment_answers"
    __table_args__ = (UniqueConstraint("attempt_id", "task_id", name="attempt_task"),)

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"), index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessment_tasks.id", ondelete="CASCADE")
    )
    # Quiz: {"selected": [bank indexes]}. Code: {"language": ..., "code": ...}.
    answer: Mapped[dict[str, Any]] = mapped_column(JSON)
    # Filled on finish: share of the task earned, 0–1.
    points: Mapped[float | None]
