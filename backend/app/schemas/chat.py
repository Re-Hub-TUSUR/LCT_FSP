import uuid
from datetime import datetime

from pydantic import Field

from app.models.enums import MeetingStatus, MessageKind
from app.schemas.common import ApiModel


class ConversationPeer(ApiModel):
    id: uuid.UUID
    name: str
    subtitle: str | None = None


class ConversationRead(ApiModel):
    id: uuid.UUID
    peer: ConversationPeer
    last_message_at: datetime | None
    matched: bool = True


class AttachmentRead(ApiModel):
    id: uuid.UUID
    filename: str
    media_type: str
    size_bytes: int


class MeetingPreview(ApiModel):
    id: uuid.UUID
    title: str
    starts_at: datetime
    ends_at: datetime
    location: str | None
    status: MeetingStatus


class MessageRead(ApiModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    kind: MessageKind
    text: str | None
    attachment: AttachmentRead | None = None
    meeting: MeetingPreview | None = None
    created_at: datetime


class MessagePage(ApiModel):
    items: list[MessageRead]
    has_more: bool


class TextMessageCreate(ApiModel):
    text: str = Field(min_length=1, max_length=4000)


class ChatMeetingCreate(ApiModel):
    location: str = Field(min_length=1, max_length=500)
    starts_at: datetime
    ends_at: datetime | None = None
    title: str = Field(default="Собеседование", max_length=200)
    vacancy_id: uuid.UUID | None = None
