"""Employer activity log and the signals it raises

Revision ID: c8d4e2a1b6f3
Revises: b7e1c9d4a2f6
Create Date: 2026-10-21 09:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c8d4e2a1b6f3"
down_revision: str | None = "b7e1c9d4a2f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "activity_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_events_user_id", "activity_events", ["user_id"])
    op.create_index("ix_activity_events_company_id", "activity_events", ["company_id"])
    op.create_index(
        "ix_activity_events_company_kind_at",
        "activity_events",
        ["company_id", "kind", "created_at"],
    )
    op.create_table(
        "admin_employer_signals",
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("hits", sa.Integer(), nullable=False),
        sa.Column("first_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("company_id", "code"),
    )


def downgrade() -> None:
    op.drop_table("admin_employer_signals")
    op.drop_index("ix_activity_events_company_kind_at", table_name="activity_events")
    op.drop_index("ix_activity_events_company_id", table_name="activity_events")
    op.drop_index("ix_activity_events_user_id", table_name="activity_events")
    op.drop_table("activity_events")
