import uuid
from datetime import datetime
from typing import Literal

from app.schemas.common import ApiModel

CalendarEventKind = Literal["interview", "assessment", "task-deadline"]


class CalendarEventRead(ApiModel):
    id: uuid.UUID
    title: str
    kind: CalendarEventKind
    starts_at: datetime
    ends_at: datetime
    invitation_id: uuid.UUID | None
