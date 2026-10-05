import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import ReactionKind


class VacancyReaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A candidate's decision on a vacancy in the feed or the swipe deck."""

    __tablename__ = "vacancy_reactions"
    __table_args__ = (UniqueConstraint("user_id", "vacancy_id"),)

    # Keyed by account, not profile: a candidate can react before filling the profile in.
    # The unique (user_id, vacancy_id) index also serves lookups by user.
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    vacancy_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vacancies.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[ReactionKind] = mapped_column(str_enum(ReactionKind))


class CandidateReaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A recruiter's decision on a candidate: favourites and «don't show again»."""

    __tablename__ = "candidate_reactions"
    __table_args__ = (UniqueConstraint("user_id", "candidate_id"),)

    # The unique (user_id, candidate_id) index also serves lookups by user.
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True
    )
    # The vacancy the recruiter was hiring for when deciding, if any.
    vacancy_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vacancies.id", ondelete="SET NULL")
    )
    kind: Mapped[ReactionKind] = mapped_column(str_enum(ReactionKind))
