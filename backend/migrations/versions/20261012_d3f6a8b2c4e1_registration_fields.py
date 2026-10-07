"""registration fields from the spec: legal details, job status, experience, vacancy terms

Existing rows are backfilled: a vacancy's single grade and stack become `grades` and
`stack_required`, and the old visibility switch becomes the job status.

Revision ID: d3f6a8b2c4e1
Revises: c7d2e9f4a6b1
Create Date: 2026-10-12 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d3f6a8b2c4e1"
down_revision: str | None = "c7d2e9f4a6b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_JSON_LIST = {"nullable": False, "server_default": "[]"}


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(length=32), nullable=True))
    op.add_column(
        "users", sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index("ix_users_last_active_at", "users", ["last_active_at"])

    op.add_column("companies", sa.Column("inn", sa.String(length=12), nullable=True))
    op.add_column("companies", sa.Column("ogrn", sa.String(length=15), nullable=True))
    op.add_column("companies", sa.Column("kpp", sa.String(length=9), nullable=True))
    op.add_column("companies", sa.Column("legal_address", sa.String(length=500), nullable=True))
    op.add_column("companies", sa.Column("logo", sa.LargeBinary(), nullable=True))
    op.add_column("companies", sa.Column("logo_type", sa.String(length=32), nullable=True))
    with op.batch_alter_table("companies", schema=None) as batch_op:
        batch_op.create_unique_constraint("uq_companies_inn", ["inn"])

    op.add_column(
        "candidate_profiles",
        sa.Column("job_status", sa.String(length=16), nullable=False, server_default="open"),
    )
    op.add_column("candidate_profiles", sa.Column("employment_types", sa.JSON(), **_JSON_LIST))
    op.add_column("candidate_profiles", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("candidate_profiles", sa.Column("experience_entries", sa.JSON(), **_JSON_LIST))
    op.add_column(
        "candidate_profiles",
        sa.Column("no_experience", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("candidate_profiles", sa.Column("education", sa.JSON(), **_JSON_LIST))
    op.add_column(
        "candidate_profiles", sa.Column("github_url", sa.String(length=300), nullable=True)
    )
    op.add_column(
        "candidate_profiles",
        sa.Column(
            "profile_display_consent", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "candidate_profiles", sa.Column("fsp_sync", sa.String(length=16), nullable=True)
    )
    profiles = sa.table(
        "candidate_profiles",
        sa.column("job_status", sa.String),
        sa.column("is_visible_to_employers", sa.Boolean),
        sa.column("profile_display_consent", sa.Boolean),
    )
    op.execute(
        profiles.update()
        .where(profiles.c.is_visible_to_employers.is_(False))
        .values(job_status="not_looking")
    )
    # Whoever had the profile visible already agreed to show it.
    op.execute(
        profiles.update()
        .where(profiles.c.is_visible_to_employers.is_(True))
        .values(profile_display_consent=True)
    )

    op.add_column("vacancies", sa.Column("grades", sa.JSON(), **_JSON_LIST))
    op.add_column("vacancies", sa.Column("stack_required", sa.JSON(), **_JSON_LIST))
    op.add_column("vacancies", sa.Column("stack_nice", sa.JSON(), **_JSON_LIST))
    op.add_column(
        "vacancies",
        sa.Column("relocation_help", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("vacancies", sa.Column("employment_types", sa.JSON(), **_JSON_LIST))
    op.add_column("vacancies", sa.Column("benefits", sa.JSON(), **_JSON_LIST))
    op.add_column(
        "vacancies",
        sa.Column("verified_grade_only", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "vacancies", sa.Column("fsp_best_result", sa.String(length=16), nullable=True)
    )
    op.add_column("vacancies", sa.Column("fsp_discipline", sa.String(length=16), nullable=True))
    op.add_column(
        "vacancies",
        sa.Column("min_experience_years", sa.Integer(), nullable=False, server_default="0"),
    )
    _backfill_vacancies()


def _backfill_vacancies() -> None:
    vacancies = sa.table(
        "vacancies",
        sa.column("id", sa.Uuid),
        sa.column("grade", sa.String),
        sa.column("stack", sa.JSON),
        sa.column("grades", sa.JSON),
        sa.column("stack_required", sa.JSON),
        sa.column("employment_types", sa.JSON),
    )
    connection = op.get_bind()
    rows = connection.execute(sa.select(vacancies.c.id, vacancies.c.grade, vacancies.c.stack))
    for vacancy_id, grade, stack in rows.all():
        connection.execute(
            vacancies.update()
            .where(vacancies.c.id == vacancy_id)
            .values(grades=[grade], stack_required=list(stack or []), employment_types=["full"])
        )


def downgrade() -> None:
    for name in (
        "min_experience_years",
        "fsp_discipline",
        "fsp_best_result",
        "verified_grade_only",
        "benefits",
        "employment_types",
        "relocation_help",
        "stack_nice",
        "stack_required",
        "grades",
    ):
        op.drop_column("vacancies", name)
    for name in (
        "fsp_sync",
        "profile_display_consent",
        "github_url",
        "education",
        "no_experience",
        "experience_entries",
        "birth_date",
        "employment_types",
        "job_status",
    ):
        op.drop_column("candidate_profiles", name)
    with op.batch_alter_table("companies", schema=None) as batch_op:
        batch_op.drop_constraint("uq_companies_inn", type_="unique")
        for name in ("logo_type", "logo", "legal_address", "kpp", "ogrn", "inn"):
            batch_op.drop_column(name)
    op.drop_index("ix_users_last_active_at", table_name="users")
    for name in ("last_active_at", "phone", "last_name", "first_name"):
        op.drop_column("users", name)
