"""Hash of a starter task's content: tells an untouched row from an edited one

Revision ID: c4e6a8b0d2f4
Revises: b3d5f7a9c1e2
Create Date: 2026-10-16 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4e6a8b0d2f4"
down_revision: str | None = "b3d5f7a9c1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("assessment_tasks", schema=None) as batch_op:
        batch_op.add_column(sa.Column("seed_hash", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("assessment_tasks", schema=None) as batch_op:
        batch_op.drop_column("seed_hash")
