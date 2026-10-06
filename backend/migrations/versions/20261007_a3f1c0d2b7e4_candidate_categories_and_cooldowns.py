"""candidate categories and per-test cooldowns

Revision ID: a3f1c0d2b7e4
Revises: 7c2d9e4a1f58
Create Date: 2026-10-07 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "a3f1c0d2b7e4"
down_revision: str | None = "7c2d9e4a1f58"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidate_categories",
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("specialization", sa.String(length=64), nullable=False),
        sa.Column(
            "grade",
            sa.Enum(
                "intern",
                "junior",
                "middle",
                "senior",
                "lead",
                name="grade",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("change_allowed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "score >= 0 AND score <= 100", name=op.f("ck_candidate_categories_score_range")
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidate_profiles.id"],
            name=op.f("fk_candidate_categories_candidate_id_candidate_profiles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_categories")),
        sa.UniqueConstraint(
            "candidate_id", "specialization", name=op.f("uq_candidate_categories_candidate_id")
        ),
    )

    with op.batch_alter_table("assessment_tests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("specialization", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("retry_days", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("grade_change_days", sa.Integer(), nullable=True))
        batch_op.create_check_constraint(
            batch_op.f("ck_assessment_tests_retry_days_positive"), "retry_days >= 0"
        )
        batch_op.create_check_constraint(
            batch_op.f("ck_assessment_tests_grade_change_days_positive"),
            "grade_change_days >= 0",
        )

    with op.batch_alter_table("assessment_attempts", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("retry_days", sa.Integer(), server_default="7", nullable=False)
        )
        batch_op.add_column(
            sa.Column("grade_change_days", sa.Integer(), server_default="90", nullable=False)
        )

    # Categories confirmed before this migration lived only in the profile.
    op.execute(
        """
        INSERT INTO candidate_categories
            (id, candidate_id, specialization, grade, score, confirmed_at, change_allowed_at)
        SELECT
            gen_random_uuid(),
            id,
            specialization,
            grade,
            assessment_score,
            COALESCE(grade_changed_at, now()),
            COALESCE(grade_changed_at, now()) + INTERVAL '90 days'
        FROM candidate_profiles
        WHERE assessment_status = 'passed'
          AND specialization IS NOT NULL
          AND grade IS NOT NULL
          AND assessment_score IS NOT NULL
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("assessment_attempts", schema=None) as batch_op:
        batch_op.drop_column("grade_change_days")
        batch_op.drop_column("retry_days")

    with op.batch_alter_table("assessment_tests", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("ck_assessment_tests_grade_change_days_positive"), type_="check"
        )
        batch_op.drop_constraint(batch_op.f("ck_assessment_tests_retry_days_positive"), type_="check")
        batch_op.drop_column("grade_change_days")
        batch_op.drop_column("retry_days")
        batch_op.drop_column("specialization")

    op.drop_table("candidate_categories")
