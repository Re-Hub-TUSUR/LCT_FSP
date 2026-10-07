"""time spent on every task of an attempt

Revision ID: b1e5f3a7c9d2
Revises: a9d4e7f2c1b8
Create Date: 2026-10-11 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "b1e5f3a7c9d2"
down_revision: str | None = "a9d4e7f2c1b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assessment_task_times",
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("seconds", sa.Float(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["assessment_attempts.id"],
            name=op.f("fk_assessment_task_times_attempt_id_assessment_attempts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("attempt_id", "task_id", name=op.f("pk_assessment_task_times")),
    )
    op.create_index(
        op.f("ix_assessment_task_times_task_id"), "assessment_task_times", ["task_id"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_assessment_task_times_task_id"), table_name="assessment_task_times")
    op.drop_table("assessment_task_times")
