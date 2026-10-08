import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import SavedSearchKind


class SavedSearch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Filters a user saved to come back to, and what of their results the user has seen.

    A result is new while it matches and is not among `seen_ids`: so a candidate counts as new
    whatever brought them in (a sign-up, a passed test, lower expectations).
    """

    __tablename__ = "saved_searches"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[SavedSearchKind] = mapped_column(str_enum(SavedSearchKind))
    title: Mapped[str] = mapped_column(String(200))
    # The search as the list's query takes it: filters plus the text, the vacancy or the mode.
    params: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    # Results shown when the search was last opened, and the ones already announced since.
    seen_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    notified_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
