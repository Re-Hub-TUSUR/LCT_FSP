"""Saved searches: filters to come back to and the results already seen

Revision ID: f2b8c4d6a1e3
Revises: e7a1c3b5d9f2
Create Date: 2026-10-14 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f2b8c4d6a1e3"
down_revision: str | None = "e7a1c3b5d9f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "saved_searches",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "candidates",
                "vacancies",
                name="savedsearchkind",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("seen_ids", sa.JSON(), nullable=False),
        sa.Column("notified_ids", sa.JSON(), nullable=False),
        sa.Column("seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_saved_searches_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_saved_searches")),
    )
    with op.batch_alter_table("saved_searches", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_saved_searches_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("saved_searches", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_saved_searches_user_id"))
    op.drop_table("saved_searches")
