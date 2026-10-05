import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import FspDiscipline, FspEventLevel


class FspAchievement(UUIDPrimaryKeyMixin, Base):
    """Candidate's result at an FSP event, mirrored from the FSP registry by `fsp_member_id`."""

    __tablename__ = "fsp_achievements"
    __table_args__ = (CheckConstraint("place IS NULL OR place > 0", name="place_positive"),)

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True
    )
    event_name: Mapped[str] = mapped_column(String(300))
    discipline: Mapped[FspDiscipline] = mapped_column(str_enum(FspDiscipline))
    level: Mapped[FspEventLevel] = mapped_column(str_enum(FspEventLevel))
    year: Mapped[int]
    # Null = took part without a prize place.
    place: Mapped[int | None]
