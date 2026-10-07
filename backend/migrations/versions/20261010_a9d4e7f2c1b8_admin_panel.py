"""admin panel: snapshots, task workflow, audit, dictionaries, moderation, company verification

Only new tables: nothing existing is altered.

Revision ID: a9d4e7f2c1b8
Revises: f2a8b3c4d5e6
Create Date: 2026-10-10 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "a9d4e7f2c1b8"
down_revision: str | None = "f2a8b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TASK_STATUS = sa.Enum(
    "draft", "active", "leaked", "archived", name="taskstatus", native_enum=False, length=16
)
_CASE_STATUS = sa.Enum(
    "flagged",
    "cleared",
    "warned",
    "restricted",
    "blocked",
    name="employercasestatus",
    native_enum=False,
    length=16,
)
_VERIFICATION_STATUS = sa.Enum(
    "pending", "approved", "rejected", name="verificationstatus", native_enum=False, length=16
)


def _timestamps() -> list[sa.Column[sa.DateTime]]:
    return [
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
    ]


def _user_fk(table: str, column: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        [column], ["users.id"], name=op.f(f"fk_{table}_{column}_users"), ondelete="SET NULL"
    )


def upgrade() -> None:
    op.create_table(
        "admin_snapshots",
        sa.Column("block", sa.String(length=64), nullable=False),
        sa.Column("filters_key", sa.String(length=255), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        _user_fk("admin_snapshots", "created_by"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_snapshots")),
    )
    op.create_index(
        "ix_admin_snapshots_block_filters",
        "admin_snapshots",
        ["block", "filters_key", "computed_at"],
    )

    op.create_table(
        "admin_task_meta",
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("status", _TASK_STATUS, nullable=False),
        sa.Column("grade", sa.String(length=16), nullable=True),
        sa.Column("variables", sa.JSON(), nullable=False),
        sa.Column("time_limit_minutes", sa.Integer(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["assessment_tasks.id"],
            name=op.f("fk_admin_task_meta_task_id_assessment_tasks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("task_id", name=op.f("pk_admin_task_meta")),
    )
    op.create_index(op.f("ix_admin_task_meta_status"), "admin_task_meta", ["status"])
    op.create_index(op.f("ix_admin_task_meta_grade"), "admin_task_meta", ["grade"])

    op.create_table(
        "admin_audit_log",
        sa.Column("entity", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        _user_fk("admin_audit_log", "actor_id"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_audit_log")),
    )
    op.create_index(
        "ix_admin_audit_log_entity", "admin_audit_log", ["entity", "entity_id", "created_at"]
    )

    op.create_table(
        "admin_parameters",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        _user_fk("admin_parameters", "updated_by"),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_admin_parameters")),
    )

    op.create_table(
        "admin_specializations",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("is_archived", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("code", name=op.f("pk_admin_specializations")),
    )

    op.create_table(
        "admin_skills",
        sa.Column("specialization_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("is_archived", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["specialization_code"],
            ["admin_specializations.code"],
            name=op.f("fk_admin_skills_specialization_code_admin_specializations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_skills")),
        sa.UniqueConstraint(
            "specialization_code", "name", name=op.f("uq_admin_skills_specialization_code")
        ),
    )

    op.create_table(
        "admin_employer_cases",
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("status", _CASE_STATUS, nullable=False),
        sa.Column("invite_limit", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_admin_employer_cases_company_id_companies"),
            ondelete="CASCADE",
        ),
        _user_fk("admin_employer_cases", "updated_by"),
        sa.PrimaryKeyConstraint("company_id", name=op.f("pk_admin_employer_cases")),
    )
    op.create_index(op.f("ix_admin_employer_cases_status"), "admin_employer_cases", ["status"])

    op.create_table(
        "admin_banlist",
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.Column("company_name", sa.String(length=200), nullable=True),
        sa.Column("inn", sa.String(length=12), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("email_domain", sa.String(length=255), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("unbanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unbanned_by", sa.Uuid(), nullable=True),
        sa.Column("unban_reason", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_admin_banlist_company_id_companies"),
            ondelete="SET NULL",
        ),
        _user_fk("admin_banlist", "created_by"),
        _user_fk("admin_banlist", "unbanned_by"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_banlist")),
    )
    for column in ("company_id", "inn", "email", "email_domain", "is_active"):
        op.create_index(op.f(f"ix_admin_banlist_{column}"), "admin_banlist", [column])

    op.create_table(
        "company_verifications",
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("status", _VERIFICATION_STATUS, nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", sa.Uuid(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_company_verifications_company_id_companies"),
            ondelete="CASCADE",
        ),
        _user_fk("company_verifications", "decided_by"),
        sa.PrimaryKeyConstraint("company_id", name=op.f("pk_company_verifications")),
    )
    op.create_index(op.f("ix_company_verifications_status"), "company_verifications", ["status"])

    op.create_table(
        "company_verification_documents",
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("uploader_id", sa.Uuid(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_company_verification_documents_company_id_companies"),
            ondelete="CASCADE",
        ),
        _user_fk("company_verification_documents", "uploader_id"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_verification_documents")),
    )
    op.create_index(
        op.f("ix_company_verification_documents_company_id"),
        "company_verification_documents",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_company_verification_documents_company_id"),
        table_name="company_verification_documents",
    )
    op.drop_table("company_verification_documents")
    op.drop_index(op.f("ix_company_verifications_status"), table_name="company_verifications")
    op.drop_table("company_verifications")
    for column in ("company_id", "inn", "email", "email_domain", "is_active"):
        op.drop_index(op.f(f"ix_admin_banlist_{column}"), table_name="admin_banlist")
    op.drop_table("admin_banlist")
    op.drop_index(op.f("ix_admin_employer_cases_status"), table_name="admin_employer_cases")
    op.drop_table("admin_employer_cases")
    op.drop_table("admin_skills")
    op.drop_table("admin_specializations")
    op.drop_table("admin_parameters")
    op.drop_index("ix_admin_audit_log_entity", table_name="admin_audit_log")
    op.drop_table("admin_audit_log")
    op.drop_index(op.f("ix_admin_task_meta_grade"), table_name="admin_task_meta")
    op.drop_index(op.f("ix_admin_task_meta_status"), table_name="admin_task_meta")
    op.drop_table("admin_task_meta")
    op.drop_index("ix_admin_snapshots_block_filters", table_name="admin_snapshots")
    op.drop_table("admin_snapshots")
