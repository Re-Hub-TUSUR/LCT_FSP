import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    false,
    text,
)
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
    # Hash of the content as the starter files had it when the row was written or last synced:
    # a row whose content still matches it follows the files, an edited one is left alone.
    # Null for rows made in the admin panel and for rows loaded before the hash existed.
    seed_hash: Mapped[str | None] = mapped_column(String(64))


class AssessmentTest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Test template: how an attempt is composed, timed and scored."""

    __tablename__ = "assessment_tests"
    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="duration_positive"),
        CheckConstraint("pass_score >= 0 AND pass_score <= 100", name="pass_score_range"),
        CheckConstraint("quiz_weight >= 0 AND quiz_weight <= 100", name="quiz_weight_range"),
        CheckConstraint("quiz_min >= 0 AND quiz_min <= 100", name="quiz_min_range"),
        CheckConstraint("retry_days >= 0", name="retry_days_positive"),
        CheckConstraint("grade_change_days >= 0", name="grade_change_days_positive"),
        CheckConstraint(
            "recommend_score >= 0 AND recommend_score <= 100", name="recommend_score_range"
        ),
    )

    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    # Platform templates only: the grade this test confirms.
    grade: Mapped[Grade | None] = mapped_column(str_enum(Grade), index=True)
    # Platform templates only: null = the test of the grade for every specialization; a set value
    # overrides it for that one specialization.
    specialization: Mapped[str | None] = mapped_column(String(64))
    duration_minutes: Mapped[int]
    pass_score: Mapped[int] = mapped_column(default=60)
    # Share of quiz questions in the score, percent; the rest belongs to code tasks.
    quiz_weight: Mapped[int] = mapped_column(default=40)
    # A pass also needs this share of the quiz right, percent, however well the code went.
    quiz_min: Mapped[int] = mapped_column(default=0, server_default="0")
    # Platform templates only: the grade is offered, but its confirmation is marked as provisional.
    is_beta: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    composition: Mapped[dict[str, Any]] = mapped_column(JSON)
    # Days before a failed test can be retaken / a confirmed grade can be changed.
    # Null = the platform defaults from the settings.
    retry_days: Mapped[int | None]
    grade_change_days: Mapped[int | None]
    # A pass with at least this score recommends (and opens) the next grade. Null = the default.
    recommend_score: Mapped[int | None]
    is_active: Mapped[bool] = mapped_column(default=True)


class AssessmentAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assessment_attempts"
    __table_args__ = (
        # One running test per candidate, whatever two simultaneous requests think.
        Index(
            "uq_assessment_attempts_running",
            "candidate_id",
            unique=True,
            postgresql_where=text("status = 'in_progress'"),
            sqlite_where=text("status = 'in_progress'"),
        ),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True
    )
    test_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assessment_tests.id", ondelete="SET NULL")
    )
    # Set when the attempt answers a test a company sent; null for a platform grade test.
    assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("test_assignments.id", ondelete="SET NULL"), index=True
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
    quiz_min: Mapped[int] = mapped_column(default=0, server_default="0")
    is_beta: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    # Cooldowns are copied too: they count from this attempt, whatever the template says later.
    retry_days: Mapped[int] = mapped_column(default=7, server_default="7")
    grade_change_days: Mapped[int] = mapped_column(default=90, server_default="90")
    recommend_score: Mapped[int] = mapped_column(default=85, server_default="85")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Ids of the variant: what the candidate has already met, for drawing the next one.
    task_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    # The variant itself, in display order, as the tasks were at the start. The attempt is
    # shown, graded and reviewed from this copy, so later edits of the bank cannot reach it.
    tasks: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, server_default=text("'[]'")
    )
    # The rules the draw had to widen because the bank ran short: see `_draw`.
    draw_notes: Mapped[list[str]] = mapped_column(JSON, default=list, server_default=text("'[]'"))
    # task id → what the task's kind fixed for this attempt (e.g. the order of quiz options).
    task_state: Mapped[dict[str, dict[str, Any]]] = mapped_column(JSON, default=dict)
    # Per-topic result, filled on finish.
    breakdown: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    runs_count: Mapped[int] = mapped_column(default=0)
    # The last execution of the candidate's code: a run during the test or a try to grade it.
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Signals for reviewers; they never change the score.
    paste_count: Mapped[int] = mapped_column(default=0)
    blur_count: Mapped[int] = mapped_column(default=0)
    # The AI interview about the candidate's code (`InterviewState`); null when there was none.
    interview: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class AssessmentTaskTime(TimestampMixin, Base):
    """Seconds one task of an attempt was on the candidate's screen, summed over visits.

    The runner reports the time when the candidate leaves the task (another task, a hidden
    tab, the finish); the total never exceeds the time since the attempt started.
    """

    __tablename__ = "assessment_task_times"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"), primary_key=True
    )
    # Id of a task in the attempt's own copy of the variant, like `AssessmentAnswer.task_id`.
    task_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, index=True)
    seconds: Mapped[float] = mapped_column(default=0.0)


class AssessmentAnswer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assessment_answers"
    __table_args__ = (UniqueConstraint("attempt_id", "task_id", name="attempt_task"),)

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"), index=True
    )
    # Id of a task in the attempt's own copy of the variant. Deliberately not a foreign key:
    # deleting a task from the bank must not delete what candidates answered.
    task_id: Mapped[uuid.UUID]
    # In the stored form of the task's kind, e.g. quiz: {"selected": [bank indexes]}.
    answer: Mapped[dict[str, Any]] = mapped_column(JSON)
    # Share of the task earned, 0–1. Filled on finish; an answer only a person can grade
    # stays null until the review.
    points: Mapped[float | None]
    # Reviewer's note to a hand-graded answer.
    comment: Mapped[str | None] = mapped_column(Text)
