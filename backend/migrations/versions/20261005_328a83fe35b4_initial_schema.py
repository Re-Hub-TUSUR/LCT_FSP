"""initial schema

Revision ID: 328a83fe35b4
Revises:
Create Date: 2026-10-05 19:26:00.937352
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "328a83fe35b4"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "candidate", "employer", "admin", name="userrole", native_enum=False, length=16
            ),
            nullable=False,
        ),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("personal_data_consent", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_users_email"), ["email"], unique=True)

    op.create_table(
        "candidate_profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("headline", sa.String(length=300), nullable=True),
        sa.Column("about", sa.Text(), nullable=True),
        sa.Column("stack", sa.JSON(), nullable=False),
        sa.Column("experience_years", sa.Integer(), nullable=True),
        sa.Column("specialization", sa.String(length=64), nullable=True),
        sa.Column(
            "grade",
            sa.Enum(
                "intern",
                "junior",
                "middle",
                "senior",
                "lead",
                name="grade",
                native_enum=False,
                length=16,
            ),
            nullable=True,
        ),
        sa.Column("grade_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fsp_member_id", sa.String(length=64), nullable=True),
        sa.Column("is_visible_to_employers", sa.Boolean(), nullable=False),
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
            name=op.f("fk_candidate_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_profiles")),
        sa.UniqueConstraint("fsp_member_id", name=op.f("uq_candidate_profiles_fsp_member_id")),
        sa.UniqueConstraint("user_id", name=op.f("uq_candidate_profiles_user_id")),
    )
    with op.batch_alter_table("candidate_profiles", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_candidate_profiles_grade"), ["grade"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_candidate_profiles_specialization"), ["specialization"], unique=False
        )

    op.create_table(
        "companies",
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("industry", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
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
            ["owner_id"], ["users.id"], name=op.f("fk_companies_owner_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_companies")),
        sa.UniqueConstraint("owner_id", name=op.f("uq_companies_owner_id")),
    )
    op.create_table(
        "vacancies",
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("specialization", sa.String(length=64), nullable=False),
        sa.Column(
            "grade",
            sa.Enum(
                "intern",
                "junior",
                "middle",
                "senior",
                "lead",
                name="grade",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("stack", sa.JSON(), nullable=False),
        sa.Column("salary_from", sa.Integer(), nullable=False),
        sa.Column("salary_to", sa.Integer(), nullable=False),
        sa.Column(
            "work_format",
            sa.Enum("office", "hybrid", "remote", name="workformat", native_enum=False, length=16),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "salary_from > 0 AND salary_from <= salary_to", name=op.f("ck_vacancies_salary_range")
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_vacancies_company_id_companies"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vacancies")),
    )
    with op.batch_alter_table("vacancies", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_vacancies_company_id"), ["company_id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_vacancies_specialization"), ["specialization"], unique=False
        )

    op.create_table(
        "invitations",
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("vacancy_id", sa.Uuid(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("salary_from", sa.Integer(), nullable=False),
        sa.Column("salary_to", sa.Integer(), nullable=False),
        sa.Column("contact_method", sa.String(length=200), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "sent",
                "viewed",
                "accepted",
                "declined",
                name="invitationstatus",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
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
        sa.CheckConstraint(
            "salary_from > 0 AND salary_from <= salary_to", name=op.f("ck_invitations_salary_range")
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidate_profiles.id"],
            name=op.f("fk_invitations_candidate_id_candidate_profiles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_invitations_company_id_companies"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vacancy_id"],
            ["vacancies.id"],
            name=op.f("fk_invitations_vacancy_id_vacancies"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_invitations")),
    )
    with op.batch_alter_table("invitations", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_invitations_candidate_id"), ["candidate_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_invitations_company_id"), ["company_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("invitations", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_invitations_company_id"))
        batch_op.drop_index(batch_op.f("ix_invitations_candidate_id"))

    op.drop_table("invitations")
    with op.batch_alter_table("vacancies", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_vacancies_specialization"))
        batch_op.drop_index(batch_op.f("ix_vacancies_company_id"))

    op.drop_table("vacancies")
    op.drop_table("companies")
    with op.batch_alter_table("candidate_profiles", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_candidate_profiles_specialization"))
        batch_op.drop_index(batch_op.f("ix_candidate_profiles_grade"))

    op.drop_table("candidate_profiles")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_email"))

    op.drop_table("users")