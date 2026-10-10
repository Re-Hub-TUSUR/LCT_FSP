import uuid
from datetime import datetime

from app.schemas.common import ApiModel, SalaryRead


class CandidateInboundRead(ApiModel):
    company_id: uuid.UUID
    company_name: str
    industry: str | None
    # The vacancy the recruiter picked the candidate for; null for a like that names none.
    vacancy_id: uuid.UUID | None
    vacancy_title: str | None = None
    salary: SalaryRead | None = None
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
