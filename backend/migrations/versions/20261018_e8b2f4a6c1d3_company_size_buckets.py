"""Company size holds only the buckets of the company form

Revision ID: e8b2f4a6c1d3
Revises: d7c1e9a4b6f2
Create Date: 2026-10-18 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e8b2f4a6c1d3"
down_revision: str | None = "d7c1e9a4b6f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SIZES = ("1-10", "11-50", "51-200", "201-500", "500+")
# The demo data was written with dashes and with buckets the form does not offer.
_RENAMED = {
    "1–10": "1-10",
    "11–50": "11-50",
    "51–200": "51-200",
    "201–500": "201-500",
    "501–1000": "500+",
    "1001–5000": "500+",
    "5000+": "500+",
}


def upgrade() -> None:
    companies = sa.table("companies", sa.column("size", sa.String))
    for old, new in _RENAMED.items():
        op.execute(companies.update().where(companies.c.size == old).values(size=new))
    # Anything else was typed past the form: there is no bucket to map it to.
    op.execute(companies.update().where(companies.c.size.notin_(_SIZES)).values(size=None))


def downgrade() -> None:
    # The free-form values are not kept, so there is nothing to restore.
    pass
