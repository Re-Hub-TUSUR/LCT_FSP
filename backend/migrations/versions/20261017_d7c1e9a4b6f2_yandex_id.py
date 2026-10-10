"""Yandex ID on the account, and a portrait waiting for the first resume save

Revision ID: d7c1e9a4b6f2
Revises: c4e6a8b0d2f4
Create Date: 2026-10-17 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d7c1e9a4b6f2"
down_revision: str | None = "c4e6a8b0d2f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("yandex_id", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("pending_photo", sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column("pending_photo_type", sa.String(length=32), nullable=True))
        batch_op.create_index("ix_users_yandex_id", ["yandex_id"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_yandex_id")
        batch_op.drop_column("pending_photo_type")
        batch_op.drop_column("pending_photo")
        batch_op.drop_column("yandex_id")
