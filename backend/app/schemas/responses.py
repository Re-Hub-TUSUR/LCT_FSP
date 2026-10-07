import uuid
from datetime import datetime

from app.schemas.common import ApiModel


class CandidateInboundRead(ApiModel):
    company_id: uuid.UUID
    company_name: str
    industry: str | None
    vacancy_id: uuid.UUID | None
    reacted_at: datetime


class EmployerInboundRead(ApiModel):
    candidate_id: uuid.UUID
    display_name: str
    headline: str | None
    vacancy_id: uuid.UUID
    vacancy_title: str
    reacted_at: datetime


class InboundRespondCandidate(ApiModel):
    company_id: uuid.UUID
    vacancy_id: uuid.UUID | None = None


class InboundRespondEmployer(ApiModel):
    candidate_id: uuid.UUID
    vacancy_id: uuid.UUID | None = None
