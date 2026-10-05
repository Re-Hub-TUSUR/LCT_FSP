from enum import StrEnum

from sqlalchemy import Enum


def str_enum(enum_cls: type[StrEnum]) -> Enum:
    """Stores enum values as VARCHAR: portable (PostgreSQL / SQLite) and migration-friendly."""
    return Enum(
        enum_cls,
        native_enum=False,
        length=16,
        values_callable=lambda members: [member.value for member in members],
    )
