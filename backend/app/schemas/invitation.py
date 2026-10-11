import uuid
from datetime import datetime

from pydantic import Field

from app.models.enums import InvitationStatus
from app.schemas.common import ApiModel, SalaryRange, SalaryRead
from app.schemas.vacancy import CompanyRef


class InvitationCreate(ApiModel):
    candidate_id: uuid.UUID
    vacancy_id: uuid.UUID | None = None
    message: str = Field(min_length=20, max_length=4000)
    salary: SalaryRange
    contact_method: str = Field(min_length=3, max_length=200)


class InvitationRead(ApiModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    company: CompanyRef
    vacancy_id: uuid.UUID | None
    # None both when no vacancy was named and when that vacancy was later deleted.
    vacancy_title: str | None
    message: str
    salary: SalaryRead
    contact_method: str
    status: InvitationStatus
    created_at: datetime
    updated_at: datetime
