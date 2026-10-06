"""additional resumes and a profile photo

Revision ID: f1a2b3c4d5e6
Revises: e4b7a9c3d1f2
Create Date: 2026-10-06 19:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: str | None = "e4b7a9c3d1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "candidate_profiles",
        sa.Column("additional_resumes", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column("candidate_profiles", sa.Column("photo", sa.LargeBinary(), nullable=True))
    op.add_column(
        "candidate_profiles", sa.Column("photo_type", sa.String(length=32), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("candidate_profiles", "photo_type")
    op.drop_column("candidate_profiles", "photo")
    op.drop_column("candidate_profiles", "additional_resumes")
