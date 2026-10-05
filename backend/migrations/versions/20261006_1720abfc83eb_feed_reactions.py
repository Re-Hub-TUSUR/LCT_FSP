"""feed reactions

Revision ID: 1720abfc83eb
Revises: ee4710a30e13
Create Date: 2026-10-06 02:03:48.915149
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "1720abfc83eb"
down_revision: str | None = "ee4710a30e13"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidate_reactions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("vacancy_id", sa.Uuid(), nullable=True),
        sa.Column(
            "kind",
            sa.Enum("like", "skip", name="reactionkind", native_enum=False, length=16),
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
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidate_profiles.id"],
            name=op.f("fk_candidate_reactions_candidate_id_candidate_profiles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_candidate_reactions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vacancy_id"],
            ["vacancies.id"],
            name=op.f("fk_candidate_reactions_vacancy_id_vacancies"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_reactions")),
        sa.UniqueConstraint("user_id", "candidate_id", name=op.f("uq_candidate_reactions_user_id")),
    )
    with op.batch_alter_table("candidate_reactions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_candidate_reactions_candidate_id"), ["candidate_id"], unique=False
        )

    op.create_table(
        "vacancy_reactions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("vacancy_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("like", "skip", name="reactionkind", native_enum=False, length=16),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_vacancy_reactions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vacancy_id"],
            ["vacancies.id"],
            name=op.f("fk_vacancy_reactions_vacancy_id_vacancies"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vacancy_reactions")),
        sa.UniqueConstraint("user_id", "vacancy_id", name=op.f("uq_vacancy_reactions_user_id")),
    )
    with op.batch_alter_table("vacancy_reactions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_vacancy_reactions_vacancy_id"), ["vacancy_id"], unique=False
        )

    with op.batch_alter_table("vacancies", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_vacancies_grade"), ["grade"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_vacancies_published_at"), ["published_at"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("vacancies", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_vacancies_published_at"))
        batch_op.drop_index(batch_op.f("ix_vacancies_grade"))

    with op.batch_alter_table("vacancy_reactions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_vacancy_reactions_vacancy_id"))

    op.drop_table("vacancy_reactions")
    with op.batch_alter_table("candidate_reactions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_candidate_reactions_candidate_id"))

    op.drop_table("candidate_reactions")
