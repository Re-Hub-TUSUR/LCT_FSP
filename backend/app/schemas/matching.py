import uuid

from pydantic import Field

from app.models.enums import Grade
from app.schemas.candidate import CandidateRead
from app.schemas.common import ApiModel


class HiringNeedCreate(ApiModel):
    """Employer's described need; the selection of candidates is built from it."""

    title: str = Field(min_length=3, max_length=200)
    team_description: str | None = None
    specialization: str
    grade: Grade
    stack: list[str] = Field(default_factory=list)


class HiringNeedRead(HiringNeedCreate):
    id: uuid.UUID


class Recommendation(ApiModel):
    candidate: CandidateRead
    score: float = Field(ge=0, le=1)
    # Explainability of the ranking (ТЗ 2.1, "обоснование попадания кандидата в подборку").
    reasons: list[str]


class RecommendationList(ApiModel):
    need_id: uuid.UUID | None
    items: list[Recommendation]
