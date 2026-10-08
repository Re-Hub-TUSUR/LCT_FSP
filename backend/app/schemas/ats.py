import uuid

from app.schemas.common import ApiModel


class AtsConnectionRead(ApiModel):
    connected: bool
    provider: str | None
    cursor: str | None


class AtsPollRead(ApiModel):
    ingested: int
    screened: int


class AtsApplicationRead(ApiModel):
    id: uuid.UUID
    external_id: str
    candidate_name: str
    job_title: str
    city: str | None
    score: int | None
    decision: str | None
    reasons: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    model_version: str | None
    synced: bool
