"""make the team's accounts admins

Promotes existing accounts only; an address that has no account yet is skipped (create it with
`python -m app.admin.create_admin`). Runs once, like every migration.

Revision ID: c7d2e9f4a6b1
Revises: b1e5f3a7c9d2
Create Date: 2026-10-11 10:05:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "c7d2e9f4a6b1"
down_revision: str | None = "b1e5f3a7c9d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ADMINS = ("skopintsevasa@yandex.ru", "hirosaq@ogzmail.com")

_users = sa.table("users", sa.column("email", sa.String), sa.column("role", sa.String))


def upgrade() -> None:
    op.execute(
        _users.update().where(sa.func.lower(_users.c.email).in_(ADMINS)).values(role="admin")
    )


def downgrade() -> None:
    # The previous roles are not stored: demoting is a decision for a person, not a rollback.
    pass
