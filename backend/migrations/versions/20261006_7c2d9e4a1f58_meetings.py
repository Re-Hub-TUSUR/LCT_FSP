"""meetings

Revision ID: 7c2d9e4a1f58
Revises: b8ac07f59b63
Create Date: 2026-10-06 18:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "7c2d9e4a1f58"
down_revision: str | None = "b8ac07f59b63"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "meetings",
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("vacancy_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(length=500), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "confirmed",
                "declined",
                name="meetingstatus",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
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
        sa.CheckConstraint("starts_at < ends_at", name=op.f("ck_meetings_time_range")),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidate_profiles.id"],
            name=op.f("fk_meetings_candidate_id_candidate_profiles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_meetings_company_id_companies"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vacancy_id"],
            ["vacancies.id"],
            name=op.f("fk_meetings_vacancy_id_vacancies"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meetings")),
    )
    with op.batch_alter_table("meetings", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_meetings_candidate_id"), ["candidate_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_meetings_company_id"), ["company_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_meetings_starts_at"), ["starts_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("meetings", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_meetings_starts_at"))
        batch_op.drop_index(batch_op.f("ix_meetings_company_id"))
        batch_op.drop_index(batch_op.f("ix_meetings_candidate_id"))

    op.drop_table("meetings")
