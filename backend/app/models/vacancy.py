import uuid
from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import FspDiscipline, FspResult, Grade, WorkFormat


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
    # The first of `grades`; kept for ranking until the matching formula reads `grades`.
    grade: Mapped[Grade] = mapped_column(str_enum(Grade), index=True)
    # `stack_required` + `stack_nice`; kept for ranking until the formula reads both.
    stack: Mapped[list[str]] = mapped_column(JSON, default=list)
    salary_from: Mapped[int]
    salary_to: Mapped[int]
    work_format: Mapped[WorkFormat] = mapped_column(str_enum(WorkFormat))
    # Office location; null for fully remote positions.
    # Canonical name. The place itself is `city_id` (GeoNames).
    city: Mapped[str | None] = mapped_column(String(100))
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.geoname_id"), index=True)
    city_country_code: Mapped[str | None] = mapped_column(String(2))
    city_region: Mapped[str | None] = mapped_column(String(200))
    city_latitude: Mapped[float | None]
    city_longitude: Mapped[float | None]
    # Null = draft, not shown in feeds.
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    # One grade or two neighbouring ones.
    grades: Mapped[list[str]] = mapped_column(JSON, default=list)
    stack_required: Mapped[list[str]] = mapped_column(JSON, default=list)
    stack_nice: Mapped[list[str]] = mapped_column(JSON, default=list)
    relocation_help: Mapped[bool] = mapped_column(default=False)
    employment_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    benefits: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Recruiter's defaults for the candidate search opened from this vacancy.
    verified_grade_only: Mapped[bool] = mapped_column(default=True)
    fsp_best_result: Mapped[FspResult | None] = mapped_column(str_enum(FspResult))
    fsp_discipline: Mapped[FspDiscipline | None] = mapped_column(str_enum(FspDiscipline))
    # 0 = any, otherwise 1, 3 or 5 years of commercial experience.
    min_experience_years: Mapped[int] = mapped_column(default=0)
