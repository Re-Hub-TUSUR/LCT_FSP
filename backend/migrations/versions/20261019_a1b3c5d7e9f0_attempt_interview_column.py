"""Ensure the AI-interview column exists on assessment attempts

Revision ID: a1b3c5d7e9f0
Revises: e8b2f4a6c1d3
Create Date: 2026-10-19 03:40:00.000000

Some databases reached head without `assessment_attempts.interview`, so reading
the grade-test status raised "column does not exist" and the client showed
«Внутренняя ошибка сервера».
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1b3c5d7e9f0"
down_revision: str | None = "e8b2f4a6c1d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE assessment_attempts ADD COLUMN IF NOT EXISTS interview JSON")


def downgrade() -> None:
    # The column belongs to d4f8a2c6e9b3. This revision only repairs databases
    # that reached head without it, so going back must not drop it.
    pass
