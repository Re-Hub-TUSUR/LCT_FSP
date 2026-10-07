"""SQL pieces whose spelling differs between PostgreSQL (production) and SQLite (tests).

Everything else in the analytics is plain SQLAlchemy Core and runs on both.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import (
    ColumnElement,
    Date,
    FromClause,
    Integer,
    Select,
    SQLColumnExpression,
    String,
    Uuid,
    and_,
    cast,
    func,
    literal,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

type Expr = SQLColumnExpression[Any]


class Dialect:
    """Builds the dialect-specific expressions. `postgresql` is the production database."""

    def __init__(self, name: str) -> None:
        self.postgres = name == "postgresql"

    @classmethod
    def of(cls, session: AsyncSession) -> "Dialect":
        return cls(session.get_bind().dialect.name)

    def json_elements(self, column: Expr) -> FromClause:
        """Rows of a JSON array of strings, one `value` column. Used as an implicitly lateral
        FROM item: both databases let the function read the table joined before it."""
        if self.postgres:
            return func.json_array_elements_text(column).table_valued("value")
        return func.json_each(column).table_valued("value")

    def uuid_of_text(self, text: Expr) -> ColumnElement[Any]:
        """A hyphenated UUID string, comparable with a `Uuid` column."""
        if self.postgres:
            return cast(text, Uuid)
        # SQLAlchemy keeps UUIDs in SQLite as 32 hex digits without hyphens.
        return func.replace(text, "-", "")

    def whole_minutes(self, seconds: Expr) -> Expr:
        """Full minutes in a non-negative number of seconds."""
        if self.postgres:
            # A cast to integer rounds in PostgreSQL; floor() truncates.
            return cast(func.floor(seconds / 60), Integer)
        # SQLite may be built without math functions; its cast truncates.
        return cast(seconds / 60, Integer)

    def week(self, column: Expr) -> Expr:
        """Monday of the week, as a date."""
        if self.postgres:
            return cast(func.date_trunc("week", column), Date)
        return func.date(column, "weekday 0", "-6 days")

    def day(self, column: Expr) -> Expr:
        if self.postgres:
            return cast(func.date_trunc("day", column), Date)
        return func.date(column)

    def month(self, column: Expr) -> Expr:
        """First day of the month, as a date."""
        if self.postgres:
            return cast(func.date_trunc("month", column), Date)
        return func.strftime("%Y-%m-01", column)

    def json_member_text(self, column: Expr, key: Expr, member: str) -> Expr:
        """`column[key][member]` as text, null when any level is missing."""
        if self.postgres:
            return column.op("->")(key).op("->>")(literal(member))
        path = literal('$."', String) + key + literal(f'".{member}', String)
        return func.json_extract(column, path)


async def medians(
    session: AsyncSession,
    dialect: Dialect,
    source: FromClause,
    value: str,
    keys: Sequence[str],
) -> dict[tuple[Any, ...], float | None]:
    """Median of `source.c[value]` per group of `keys`, nulls ignored.

    PostgreSQL uses `percentile_cont`; SQLite has no percentile functions, so the middle rows
    are picked with window functions. The database returns one row per group either way.
    """
    group = [source.c[key] for key in keys]
    column = source.c[value]
    statement: Select[Any]
    if dialect.postgres:
        statement = (
            select(*group, func.percentile_cont(0.5).within_group(column).label("median"))
            .where(column.is_not(None))
            .group_by(*group)
        )
    else:
        ranked = (
            select(
                *group,
                column.label("value"),
                func.row_number()
                .over(partition_by=group or None, order_by=column)
                .label("position"),
                func.count().over(partition_by=group or None).label("size"),
            )
            .where(column.is_not(None))
            .subquery()
        )
        ranked_group = [ranked.c[key] for key in keys]
        size = ranked.c.size
        statement = (
            select(*ranked_group, func.avg(ranked.c.value).label("median"))
            .where(
                # The middle row of an odd group, the two middle rows of an even one.
                and_(
                    ranked.c.position >= (size + 1) // 2,
                    ranked.c.position <= (size + 2) // 2,
                )
            )
            .group_by(*ranked_group)
        )
    rows = (await session.execute(statement)).all()
    return {
        tuple(row[: len(keys)]): (float(row[-1]) if row[-1] is not None else None) for row in rows
    }
