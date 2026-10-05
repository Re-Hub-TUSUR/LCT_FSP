"""email verification codes

Revision ID: c4e8a1b09d22
Revises: 328a83fe35b4
Create Date: 2026-10-05 20:50:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4e8a1b09d22"
down_revision: str | None = "328a83fe35b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Accounts created before email codes existed can keep signing in.
    op.execute("UPDATE users SET is_email_verified = true WHERE is_email_verified = false")
    op.create_table(
        "email_verification_codes",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_email_verification_codes_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_email_verification_codes")),
        sa.UniqueConstraint("user_id", name=op.f("uq_email_verification_codes_user_id")),
    )


def downgrade() -> None:
    op.drop_table("email_verification_codes")
