import uuid
from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.common import ApiModel

ApplicationStatus = Literal["sent", "viewed", "accepted", "declined"]


class ApplicationCreate(ApiModel):
    vacancy_id: uuid.UUID
    cover_letter: str | None = Field(default=None, max_length=4000)


class ApplicationRead(ApiModel):
    id: uuid.UUID
    vacancy_id: uuid.UUID
    status: ApplicationStatus
    created_at: datetime
