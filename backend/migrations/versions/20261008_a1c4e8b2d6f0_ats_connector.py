"""ATS connector tables: connections, raw polls, the screening queue and results

Revision ID: a1c4e8b2d6f0
Revises: f2b8c4d6a1e3
Create Date: 2026-10-08 23:50:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1c4e8b2d6f0"
down_revision: str | None = "f2b8c4d6a1e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ats_connections",
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("cursor", sa.String(length=200), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_ats_connections_company_id_companies"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ats_connections")),
        sa.UniqueConstraint("company_id", name=op.f("uq_ats_connections_company_id")),
    )
    op.create_table(
        "ats_jobs",
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("required_skills", sa.JSON(), nullable=False),
        sa.Column("salary_from", sa.Integer(), nullable=True),
        sa.Column("salary_to", sa.Integer(), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["connection_id"],
            ["ats_connections.id"],
            name=op.f("fk_ats_jobs_connection_id_ats_connections"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ats_jobs")),
        sa.UniqueConstraint(
            "connection_id", "external_id", name=op.f("uq_ats_jobs_connection_id")
        ),
    )
    op.create_index(op.f("ix_ats_jobs_connection_id"), "ats_jobs", ["connection_id"])
    op.create_table(
        "ats_candidates",
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("experience_years", sa.Integer(), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("salary_expectation", sa.Integer(), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["connection_id"],
            ["ats_connections.id"],
            name=op.f("fk_ats_candidates_connection_id_ats_connections"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ats_candidates")),
        sa.UniqueConstraint(
            "connection_id", "external_id", name=op.f("uq_ats_candidates_connection_id")
        ),
    )
    op.create_index(op.f("ix_ats_candidates_connection_id"), "ats_candidates", ["connection_id"])
    op.create_table(
        "ats_applications",
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["ats_candidates.id"],
            name=op.f("fk_ats_applications_candidate_id_ats_candidates"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["connection_id"],
            ["ats_connections.id"],
            name=op.f("fk_ats_applications_connection_id_ats_connections"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["ats_jobs.id"], name=op.f("fk_ats_applications_job_id_ats_jobs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ats_applications")),
        sa.UniqueConstraint(
            "connection_id", "external_id", name=op.f("uq_ats_applications_connection_id")
        ),
    )
    op.create_index(
        op.f("ix_ats_applications_connection_id"), "ats_applications", ["connection_id"]
    )
    op.create_table(
        "ats_raw_events",
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("external_event_id", sa.String(length=128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["ats_applications.id"],
            name=op.f("fk_ats_raw_events_application_id_ats_applications"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["connection_id"],
            ["ats_connections.id"],
            name=op.f("fk_ats_raw_events_connection_id_ats_connections"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ats_raw_events")),
        sa.UniqueConstraint(
            "connection_id",
            "provider",
            "external_event_id",
            name="uq_ats_raw_events_provider_event",
        ),
    )
    op.create_index(op.f("ix_ats_raw_events_connection_id"), "ats_raw_events", ["connection_id"])
    op.create_table(
        "screening_jobs",
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "queued", "running", "done", "failed",
                name="screeningjobstatus", native_enum=False, length=16,
            ),
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["ats_applications.id"],
            name=op.f("fk_screening_jobs_application_id_ats_applications"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_screening_jobs")),
        sa.UniqueConstraint("application_id", name=op.f("uq_screening_jobs_application_id")),
    )
    op.create_index(op.f("ix_screening_jobs_status"), "screening_jobs", ["status"])
    op.create_table(
        "screening_results",
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column(
            "decision",
            sa.Enum(
                "pass", "reject", "review",
                name="screeningdecision", native_enum=False, length=16,
            ),
            nullable=False,
        ),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("matched_skills", sa.JSON(), nullable=False),
        sa.Column("missing_skills", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["ats_applications.id"],
            name=op.f("fk_screening_results_application_id_ats_applications"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_screening_results")),
    )
    op.create_index(
        op.f("ix_screening_results_application_id"), "screening_results", ["application_id"]
    )
    op.create_table(
        "ats_sync_log",
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("tag", "note", "score", name="atssynckind", native_enum=False, length=16),
            nullable=False,
        ),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["ats_applications.id"],
            name=op.f("fk_ats_sync_log_application_id_ats_applications"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ats_sync_log")),
    )
    op.create_index(op.f("ix_ats_sync_log_application_id"), "ats_sync_log", ["application_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ats_sync_log_application_id"), table_name="ats_sync_log")
    op.drop_table("ats_sync_log")
    op.drop_index(op.f("ix_screening_results_application_id"), table_name="screening_results")
    op.drop_table("screening_results")
    op.drop_index(op.f("ix_screening_jobs_status"), table_name="screening_jobs")
    op.drop_table("screening_jobs")
    op.drop_index(op.f("ix_ats_raw_events_connection_id"), table_name="ats_raw_events")
    op.drop_table("ats_raw_events")
    op.drop_index(op.f("ix_ats_applications_connection_id"), table_name="ats_applications")
    op.drop_table("ats_applications")
    op.drop_index(op.f("ix_ats_candidates_connection_id"), table_name="ats_candidates")
    op.drop_table("ats_candidates")
    op.drop_index(op.f("ix_ats_jobs_connection_id"), table_name="ats_jobs")
    op.drop_table("ats_jobs")
    op.drop_table("ats_connections")
