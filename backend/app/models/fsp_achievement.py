import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import (
    FspDiscipline,
    FspEventKind,
    FspEventLevel,
    FspOutcome,
    FspParticipation,
    FspTitleKind,
)


class FspAchievement(UUIDPrimaryKeyMixin, Base):
    """Candidate's result at an FSP event, mirrored from the FSP registry by `fsp_member_id`."""

    __tablename__ = "fsp_achievements"
    __table_args__ = (
        CheckConstraint("place IS NULL OR place > 0", name="place_positive"),
        UniqueConstraint("candidate_id", "external_id", name="uq_fsp_achievements_external"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True
    )
    # Id of the record in the FSP registry: a re-sync updates the row instead of duplicating it.
    external_id: Mapped[str] = mapped_column(String(64))
    event_name: Mapped[str] = mapped_column(String(300))
    event_kind: Mapped[FspEventKind] = mapped_column(str_enum(FspEventKind))
    discipline: Mapped[FspDiscipline] = mapped_column(str_enum(FspDiscipline))
    level: Mapped[FspEventLevel] = mapped_column(str_enum(FspEventLevel))
    year: Mapped[int]
    # Null = took part without a place.
    place: Mapped[int | None]
    result: Mapped[FspOutcome] = mapped_column(str_enum(FspOutcome))
    participation: Mapped[FspParticipation] = mapped_column(str_enum(FspParticipation))
    team_name: Mapped[str | None] = mapped_column(String(200))


class FspSportTitle(UUIDPrimaryKeyMixin, Base):
    """A sport rank or title in sport programming, as confirmed by the FSP registry."""

    __tablename__ = "fsp_sport_titles"
    __table_args__ = (
        UniqueConstraint("candidate_id", "external_id", name="uq_fsp_sport_titles_external"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(64))
    kind: Mapped[FspTitleKind] = mapped_column(str_enum(FspTitleKind))
    discipline: Mapped[FspDiscipline] = mapped_column(str_enum(FspDiscipline))
    awarded_year: Mapped[int]
