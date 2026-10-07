"""AI interview of a grade test attempt

The `interview` status needs no schema change: statuses are stored as VARCHAR(16).

Revision ID: d4f8a2c6e9b3
Revises: c7d2e9f4a6b1
Create Date: 2026-10-12 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4f8a2c6e9b3"
down_revision: str | None = "c7d2e9f4a6b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("assessment_attempts", sa.Column("interview", sa.JSON(), nullable=True))


def downgrade() -> None:
    # An attempt waiting for its interview has no meaning without it: it is a pass on points.
    op.execute(
        "UPDATE assessment_attempts SET status = 'passed' WHERE status = 'interview'"
    )
    op.drop_column("assessment_attempts", "interview")
