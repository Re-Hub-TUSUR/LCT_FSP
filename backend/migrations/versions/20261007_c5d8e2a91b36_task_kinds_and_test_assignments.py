"""task kinds registry and test assignments

Revision ID: c5d8e2a91b36
Revises: a3f1c0d2b7e4
Create Date: 2026-10-07 14:00:00.000000
"""

from collections.abc import Callable, Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op


revision: str = "c5d8e2a91b36"
down_revision: str | None = "a3f1c0d2b7e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_attempts = sa.table(
    "assessment_attempts", sa.column("id", sa.Uuid()), sa.column("task_state", sa.JSON())
)


def _rewrite_task_state(convert: Callable[[Any], Any]) -> None:
    connection = op.get_bind()
    rows = connection.execute(sa.select(_attempts.c.id, _attempts.c.task_state)).all()
    for attempt_id, state in rows:
        connection.execute(
            _attempts.update()
            .where(_attempts.c.id == attempt_id)
            .values(task_state={key: convert(value) for key, value in (state or {}).items()})
        )


def upgrade() -> None:
    op.create_table(
        "test_assignments",
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("test_id", sa.Uuid(), nullable=True),
        sa.Column("vacancy_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("tasks_count", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "sent",
                "in_progress",
                "review",
                "done",
                "declined",
                "expired",
                name="assignmentstatus",
                native_enum=False,
                length=16,
            ),
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
            name=op.f("fk_test_assignments_candidate_id_candidate_profiles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_test_assignments_company_id_companies"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["test_id"],
            ["assessment_tests.id"],
            name=op.f("fk_test_assignments_test_id_assessment_tests"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["vacancy_id"],
            ["vacancies.id"],
            name=op.f("fk_test_assignments_vacancy_id_vacancies"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_assignments")),
    )
    with op.batch_alter_table("test_assignments", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_test_assignments_candidate_id"), ["candidate_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_test_assignments_company_id"), ["company_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_test_assignments_status"), ["status"], unique=False)

    with op.batch_alter_table("assessment_attempts", schema=None) as batch_op:
        batch_op.alter_column("option_orders", new_column_name="task_state")
        batch_op.add_column(sa.Column("assignment_id", sa.Uuid(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_assessment_attempts_assignment_id"), ["assignment_id"], unique=False
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_assessment_attempts_assignment_id_test_assignments"),
            "test_assignments",
            ["assignment_id"],
            ["id"],
            ondelete="SET NULL",
        )
    # The order of quiz options used to be the whole per-task state; now every kind keeps its
    # own dictionary there.
    _rewrite_task_state(lambda value: {"order": value} if isinstance(value, list) else value)

    with op.batch_alter_table("assessment_answers", schema=None) as batch_op:
        batch_op.add_column(sa.Column("comment", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("assessment_answers", schema=None) as batch_op:
        batch_op.drop_column("comment")

    _rewrite_task_state(lambda value: value.get("order", []) if isinstance(value, dict) else value)
    with op.batch_alter_table("assessment_attempts", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_assessment_attempts_assignment_id_test_assignments"),
            type_="foreignkey",
        )
        batch_op.drop_index(batch_op.f("ix_assessment_attempts_assignment_id"))
        batch_op.drop_column("assignment_id")
        batch_op.alter_column("task_state", new_column_name="option_orders")

    with op.batch_alter_table("test_assignments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_test_assignments_status"))
        batch_op.drop_index(batch_op.f("ix_test_assignments_company_id"))
        batch_op.drop_index(batch_op.f("ix_test_assignments_candidate_id"))

    op.drop_table("test_assignments")
