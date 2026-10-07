import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import str_enum
from app.models.enums import MessageKind


class Conversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One thread per company–candidate pair after mutual interest."""

    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("company_id", "candidate_id"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class MessageAttachment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "message_attachments"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    uploader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(String(500))


class Message(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[MessageKind] = mapped_column(str_enum(MessageKind))
    text: Mapped[str | None] = mapped_column(Text)
    attachment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("message_attachments.id", ondelete="SET NULL")
    )
    meeting_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("meetings.id", ondelete="SET NULL")
    )
