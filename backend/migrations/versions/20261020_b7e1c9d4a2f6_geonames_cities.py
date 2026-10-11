"""GeoNames cities and the place stored on a resume or a vacancy

Revision ID: b7e1c9d4a2f6
Revises: a1b3c5d7e9f0
Create Date: 2026-10-20 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7e1c9d4a2f6"
down_revision: str | None = "a1b3c5d7e9f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cities",
        sa.Column("geoname_id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("region", sa.String(200), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("feature_class", sa.String(1), nullable=False),
        sa.Column("feature_code", sa.String(10), nullable=False),
        sa.Column("population", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_cities_country_code", "cities", ["country_code"])
    op.create_table(
        "city_aliases",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "city_id",
            sa.Integer(),
            sa.ForeignKey("cities.geoname_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("norm", sa.String(200), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_city_aliases_city_id", "city_aliases", ["city_id"])
    op.create_index("ix_city_aliases_norm", "city_aliases", ["norm"])
    op.create_table(
        "city_resolution_gaps",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("entity", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("raw_value", sa.Text(), nullable=False),
    )
    op.create_index("ix_city_resolution_gaps_entity_id", "city_resolution_gaps", ["entity_id"])
    for table in ("candidate_profiles", "vacancies"):
        op.add_column(table, sa.Column("city_id", sa.Integer(), nullable=True))
        op.add_column(table, sa.Column("city_country_code", sa.String(2), nullable=True))
        op.add_column(table, sa.Column("city_region", sa.String(200), nullable=True))
        op.add_column(table, sa.Column("city_latitude", sa.Float(), nullable=True))
        op.add_column(table, sa.Column("city_longitude", sa.Float(), nullable=True))
        op.create_index(f"ix_{table}_city_id", table, ["city_id"])
        op.create_foreign_key(
            f"fk_{table}_city_id", table, "cities", ["city_id"], ["geoname_id"]
        )


def downgrade() -> None:
    for table in ("vacancies", "candidate_profiles"):
        op.drop_constraint(f"fk_{table}_city_id", table, type_="foreignkey")
        op.drop_index(f"ix_{table}_city_id", table_name=table)
        op.drop_column(table, "city_longitude")
        op.drop_column(table, "city_latitude")
        op.drop_column(table, "city_region")
        op.drop_column(table, "city_country_code")
        op.drop_column(table, "city_id")
    op.drop_table("city_resolution_gaps")
    op.drop_table("city_aliases")
    op.drop_table("cities")
