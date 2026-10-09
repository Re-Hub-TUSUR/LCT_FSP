"""Minimum share of quiz answers, beta marker of a grade test, notes of a widened variant

A pass needs `quiz_min` percent of the quiz right whatever the code earned; a template marked
beta passes its mark on to the attempt and to the confirmed category; `draw_notes` keeps the
rules that had to be widened while the variant was drawn.

Revision ID: b3d5f7a9c1e2
Revises: a1c4e8b2d6f0
Create Date: 2026-10-15 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b3d5f7a9c1e2"
down_revision: str | None = "a1c4e8b2d6f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("assessment_tests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("quiz_min", sa.Integer(), server_default="0", nullable=False))
        batch_op.add_column(
            sa.Column("is_beta", sa.Boolean(), server_default=sa.false(), nullable=False)
        )
        batch_op.create_check_constraint(
            batch_op.f("ck_assessment_tests_quiz_min_range"),
            "quiz_min >= 0 AND quiz_min <= 100",
        )

    with op.batch_alter_table("assessment_attempts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("quiz_min", sa.Integer(), server_default="0", nullable=False))
        batch_op.add_column(
            sa.Column("is_beta", sa.Boolean(), server_default=sa.false(), nullable=False)
        )
        batch_op.add_column(
            sa.Column("draw_notes", sa.JSON(), server_default=sa.text("'[]'"), nullable=False)
        )

    with op.batch_alter_table("candidate_categories", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("is_beta", sa.Boolean(), server_default=sa.false(), nullable=False)
        )

    with op.batch_alter_table("candidate_profiles", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("assessment_beta", sa.Boolean(), server_default=sa.false(), nullable=False)
        )


def downgrade() -> None:
    with op.batch_alter_table("candidate_profiles", schema=None) as batch_op:
        batch_op.drop_column("assessment_beta")

    with op.batch_alter_table("candidate_categories", schema=None) as batch_op:
        batch_op.drop_column("is_beta")

    with op.batch_alter_table("assessment_attempts", schema=None) as batch_op:
        batch_op.drop_column("draw_notes")
        batch_op.drop_column("is_beta")
        batch_op.drop_column("quiz_min")

    with op.batch_alter_table("assessment_tests", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("ck_assessment_tests_quiz_min_range"), type_="check")
        batch_op.drop_column("is_beta")
        batch_op.drop_column("quiz_min")
