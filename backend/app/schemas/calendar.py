import uuid
from datetime import datetime, timedelta
from typing import Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from app.models.enums import MeetingStatus
from app.schemas.common import ApiModel

CalendarEventKind = Literal["interview", "assessment", "task-deadline"]

MAX_MEETING_DURATION = timedelta(hours=8)


class CalendarParty(ApiModel):
    """The other side of an event, or the vacancy it is about: enough for a label and a link."""

    id: uuid.UUID
    name: str


class CalendarEventRead(ApiModel):
    id: uuid.UUID
    title: str
    kind: CalendarEventKind
    starts_at: datetime
    ends_at: datetime
    invitation_id: uuid.UUID | None
    status: MeetingStatus
    company: CalendarParty
    candidate: CalendarParty
    vacancy: CalendarParty | None
    location: str | None
    note: str | None


class MeetingUpdate(ApiModel):
    """What the employer can change later; a new time asks the candidate to confirm again."""

    title: str = Field(default="Собеседование", min_length=1, max_length=200)
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    vacancy_id: uuid.UUID | None = None
    location: str | None = Field(default=None, max_length=500)
    note: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _time_range(self) -> Self:
        if self.ends_at <= self.starts_at:
            msg = "endsAt must be later than startsAt"
            raise ValueError(msg)
        if self.ends_at - self.starts_at > MAX_MEETING_DURATION:
            msg = "a meeting must not be longer than 8 hours"
            raise ValueError(msg)
        return self


class MeetingCreate(MeetingUpdate):
    candidate_id: uuid.UUID
