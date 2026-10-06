"""attempt snapshots, one running attempt, next-grade recommendation

Revision ID: e4b7a9c3d1f2
Revises: c5d8e2a91b36
Create Date: 2026-10-08 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "e4b7a9c3d1f2"
down_revision: str | None = "c5d8e2a91b36"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_GRADE = sa.Enum(
    "intern", "junior", "middle", "senior", "lead", name="grade", native_enum=False, length=16
)
_RUNNING = sa.text("status = 'in_progress'")


def _snapshot_existing_attempts() -> None:
    """Attempts used to read their tasks from the bank; copy what the bank holds now."""
    connection = op.get_bind()
    tasks = sa.table(
        "assessment_tasks",
        sa.column("id", sa.Uuid()),
        sa.column("kind", sa.String()),
        sa.column("topic", sa.String()),
        sa.column("difficulty", sa.String()),
        sa.column("title", sa.String()),
        sa.column("statement", sa.Text()),
        sa.column("payload", sa.JSON()),
    )
    attempts = sa.table(
        "assessment_attempts",
        sa.column("id", sa.Uuid()),
        sa.column("task_ids", sa.JSON()),
        sa.column("tasks", sa.JSON()),
    )
    bank = {
        str(row.id): {
            "id": str(row.id),
            "kind": row.kind,
            "topic": row.topic,
            "difficulty": row.difficulty,
            "title": row.title,
            "statement": row.statement,
            "payload": row.payload,
        }
        for row in connection.execute(sa.select(tasks))
    }
    for attempt_id, task_ids in connection.execute(
        sa.select(attempts.c.id, attempts.c.task_ids)
    ).all():
        # A task already deleted from the bank is gone for good, as it was before.
        variant = [bank[task_id] for task_id in task_ids or [] if task_id in bank]
        connection.execute(
            attempts.update().where(attempts.c.id == attempt_id).values(tasks=variant)
        )


def upgrade() -> None:
    with op.batch_alter_table("assessment_tests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("recommend_score", sa.Integer(), nullable=True))
        batch_op.create_check_constraint(
            batch_op.f("ck_assessment_tests_recommend_score_range"),
            "recommend_score >= 0 AND recommend_score <= 100",
        )

    with op.batch_alter_table("candidate_categories", schema=None) as batch_op:
        batch_op.add_column(sa.Column("recommended_grade", _GRADE, nullable=True))

    with op.batch_alter_table("assessment_attempts", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("tasks", sa.JSON(), server_default=sa.text("'[]'"), nullable=False)
        )
        batch_op.add_column(
            sa.Column("recommend_score", sa.Integer(), server_default="85", nullable=False)
        )
    _snapshot_existing_attempts()

    # Twins left by simultaneous starts would break the index: the newest one stays running.
    op.execute(
        """
        UPDATE assessment_attempts
        SET status = 'expired', finished_at = expires_at
        WHERE status = 'in_progress'
          AND id NOT IN (
              SELECT DISTINCT ON (candidate_id) id
              FROM assessment_attempts
              WHERE status = 'in_progress'
              ORDER BY candidate_id, started_at DESC, id
          )
        """
    )
    op.create_index(
        "uq_assessment_attempts_running",
        "assessment_attempts",
        ["candidate_id"],
        unique=True,
        postgresql_where=_RUNNING,
        sqlite_where=_RUNNING,
    )

    # Answers now refer to the attempt's own copy of the task, not to the bank.
    with op.batch_alter_table("assessment_answers", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_assessment_answers_task_id_assessment_tasks"), type_="foreignkey"
        )


def downgrade() -> None:
    # The foreign key cannot hold answers to tasks that have left the bank since.
    op.execute(
        "DELETE FROM assessment_answers WHERE task_id NOT IN (SELECT id FROM assessment_tasks)"
    )
    with op.batch_alter_table("assessment_answers", schema=None) as batch_op:
        batch_op.create_foreign_key(
            batch_op.f("fk_assessment_answers_task_id_assessment_tasks"),
            "assessment_tasks",
            ["task_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.drop_index(
        "uq_assessment_attempts_running",
        table_name="assessment_attempts",
        postgresql_where=_RUNNING,
        sqlite_where=_RUNNING,
    )
    # No older status exists for an attempt waiting for the code runner.
    op.execute("UPDATE assessment_attempts SET status = 'expired' WHERE status = 'grading'")
    with op.batch_alter_table("assessment_attempts", schema=None) as batch_op:
        batch_op.drop_column("recommend_score")
        batch_op.drop_column("tasks")

    with op.batch_alter_table("candidate_categories", schema=None) as batch_op:
        batch_op.drop_column("recommended_grade")

    with op.batch_alter_table("assessment_tests", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("ck_assessment_tests_recommend_score_range"), type_="check"
        )
        batch_op.drop_column("recommend_score")
