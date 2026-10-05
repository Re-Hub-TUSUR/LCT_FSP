import uuid
from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import Grade, WorkFormat


class Vacancy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vacancies"
    # Salary range in RUB is mandatory for every vacancy (ТЗ 2.2, item 1).
    __table_args__ = (
        CheckConstraint("salary_from > 0 AND salary_from <= salary_to", name="salary_range"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    specialization: Mapped[str] = mapped_column(String(64), index=True)
    grade: Mapped[Grade] = mapped_column(str_enum(Grade))
    stack: Mapped[list[str]] = mapped_column(JSON, default=list)
    salary_from: Mapped[int]
    salary_to: Mapped[int]
    work_format: Mapped[WorkFormat] = mapped_column(str_enum(WorkFormat))
    # Office location; null for fully remote positions.
    city: Mapped[str | None] = mapped_column(String(100))
    # Null = draft, not shown in feeds.
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
