"""FSP registry sync: richer achievements, sport titles, link and sync timestamps

Existing achievements are backfilled: the registry id becomes the row id, the result follows
the place, the event kind is read from the event name, and every result counts as individual.

Revision ID: e7a1c3b5d9f2
Revises: d3f6a8b2c4e1
Create Date: 2026-10-13 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e7a1c3b5d9f2"
down_revision: str | None = "d3f6a8b2c4e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_ACHIEVEMENT_COLUMNS = ("external_id", "event_kind", "result", "participation")


def upgrade() -> None:
    with op.batch_alter_table("fsp_achievements", schema=None) as batch_op:
        batch_op.add_column(sa.Column("external_id", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("event_kind", sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column("result", sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column("participation", sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column("team_name", sa.String(length=200), nullable=True))
    _backfill_achievements()
    with op.batch_alter_table("fsp_achievements", schema=None) as batch_op:
        for name in _NEW_ACHIEVEMENT_COLUMNS:
            batch_op.alter_column(name, existing_type=sa.String(), nullable=False)
        batch_op.create_unique_constraint(
            batch_op.f("uq_fsp_achievements_external"), ["candidate_id", "external_id"]
        )

    op.create_table(
        "fsp_sport_titles",
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "rank_3",
                "rank_2",
                "rank_1",
                "kms",
                "ms",
                "msmk",
                "zms",
                name="fsptitlekind",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column(
            "discipline",
            sa.Enum(
                "algorithmic",
                "product",
                "security",
                "robotics",
                "uav",
                name="fspdiscipline",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("awarded_year", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidate_profiles.id"],
            name=op.f("fk_fsp_sport_titles_candidate_id_candidate_profiles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fsp_sport_titles")),
        sa.UniqueConstraint(
            "candidate_id", "external_id", name=op.f("uq_fsp_sport_titles_external")
        ),
    )
    with op.batch_alter_table("fsp_sport_titles", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_fsp_sport_titles_candidate_id"), ["candidate_id"], unique=False
        )

    with op.batch_alter_table("candidate_profiles", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("fsp_linked_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("fsp_synced_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("fsp_sync_error", sa.String(length=300), nullable=True))


def _event_kind(name: str) -> str:
    lowered = name.casefold()
    if "кубок" in lowered:
        return "cup"
    if "хакатон" in lowered:
        return "hackathon"
    if "олимпиад" in lowered:
        return "olympiad"
    return "championship"


def _result(place: int | None) -> str:
    if place is None:
        return "participant"
    if place == 1:
        return "winner"
    if place <= 3:  # noqa: PLR2004 - podium
        return "prizewinner"
    return "finalist"


def _backfill_achievements() -> None:
    achievements = sa.table(
        "fsp_achievements",
        sa.column("id", sa.Uuid),
        sa.column("event_name", sa.String),
        sa.column("place", sa.Integer),
        sa.column("external_id", sa.String),
        sa.column("event_kind", sa.String),
        sa.column("result", sa.String),
        sa.column("participation", sa.String),
    )
    connection = op.get_bind()
    rows = connection.execute(
        sa.select(achievements.c.id, achievements.c.event_name, achievements.c.place)
    )
    for achievement_id, event_name, place in rows.all():
        connection.execute(
            achievements.update()
            .where(achievements.c.id == achievement_id)
            .values(
                external_id=str(achievement_id),
                event_kind=_event_kind(event_name),
                result=_result(place),
                participation="individual",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("candidate_profiles", schema=None) as batch_op:
        for name in ("fsp_sync_error", "fsp_synced_at", "fsp_linked_at"):
            batch_op.drop_column(name)

    with op.batch_alter_table("fsp_sport_titles", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_fsp_sport_titles_candidate_id"))
    op.drop_table("fsp_sport_titles")

    with op.batch_alter_table("fsp_achievements", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_fsp_achievements_external"), type_="unique")
        for name in ("team_name", *reversed(_NEW_ACHIEVEMENT_COLUMNS)):
            batch_op.drop_column(name)
