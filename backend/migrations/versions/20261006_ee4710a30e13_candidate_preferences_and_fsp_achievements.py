"""candidate preferences and fsp achievements

Revision ID: ee4710a30e13
Revises: c4e8a1b09d22
Create Date: 2026-10-06 01:18:08.181094
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "ee4710a30e13"
down_revision: str | None = "c4e8a1b09d22"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fsp_achievements",
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("event_name", sa.String(length=300), nullable=False),
        sa.Column(
            "discipline",
            sa.Enum(
                "algorithmic",
                "product",
                "security",
                "robotics",
                "uav",
                name="fspdiscipline",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column(
            "level",
            sa.Enum(
                "regional",
                "national",
                "international",
                name="fspeventlevel",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("place", sa.Integer(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "place IS NULL OR place > 0", name=op.f("ck_fsp_achievements_place_positive")
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidate_profiles.id"],
            name=op.f("fk_fsp_achievements_candidate_id_candidate_profiles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fsp_achievements")),
    )
    with op.batch_alter_table("fsp_achievements", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_fsp_achievements_candidate_id"), ["candidate_id"], unique=False
        )

    # Server defaults only fill existing rows; the ORM sets the values for new ones.
    with op.batch_alter_table("candidate_profiles", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("soft_skills", sa.JSON(), nullable=False, server_default=sa.text("'[]'"))
        )
        batch_op.add_column(sa.Column("english_level", sa.String(length=2), nullable=True))
        batch_op.add_column(sa.Column("city", sa.String(length=100), nullable=True))
        batch_op.add_column(
            sa.Column("relocation_ready", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.add_column(
            sa.Column("work_formats", sa.JSON(), nullable=False, server_default=sa.text("'[]'"))
        )
        batch_op.add_column(sa.Column("salary_expectation", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("assessment_score", sa.Double(), nullable=True))
        batch_op.add_column(sa.Column("phone", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("telegram", sa.String(length=64), nullable=True))
        batch_op.create_check_constraint(
            op.f("ck_candidate_profiles_assessment_score_range"),
            "assessment_score >= 0 AND assessment_score <= 100",
        )
        batch_op.create_check_constraint(
            op.f("ck_candidate_profiles_salary_expectation_positive"), "salary_expectation > 0"
        )

    with op.batch_alter_table("candidate_profiles", schema=None) as batch_op:
        batch_op.alter_column("soft_skills", server_default=None)
        batch_op.alter_column("relocation_ready", server_default=None)
        batch_op.alter_column("work_formats", server_default=None)

    with op.batch_alter_table("companies", schema=None) as batch_op:
        batch_op.add_column(sa.Column("city", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("size", sa.String(length=16), nullable=True))

    with op.batch_alter_table("vacancies", schema=None) as batch_op:
        batch_op.add_column(sa.Column("city", sa.String(length=100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("vacancies", schema=None) as batch_op:
        batch_op.drop_column("city")

    with op.batch_alter_table("companies", schema=None) as batch_op:
        batch_op.drop_column("size")
        batch_op.drop_column("city")

    with op.batch_alter_table("candidate_profiles", schema=None) as batch_op:
        batch_op.drop_constraint(
            op.f("ck_candidate_profiles_salary_expectation_positive"), type_="check"
        )
        batch_op.drop_constraint(op.f("ck_candidate_profiles_assessment_score_range"), type_="check")
        batch_op.drop_column("telegram")
        batch_op.drop_column("phone")
        batch_op.drop_column("assessment_score")
        batch_op.drop_column("salary_expectation")
        batch_op.drop_column("work_formats")
        batch_op.drop_column("relocation_ready")
        batch_op.drop_column("city")
        batch_op.drop_column("english_level")
        batch_op.drop_column("soft_skills")

    with op.batch_alter_table("fsp_achievements", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_fsp_achievements_candidate_id"))

    op.drop_table("fsp_achievements")
