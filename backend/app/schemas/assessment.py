import uuid
from datetime import datetime
from typing import Any, Literal

from app.models.enums import Grade
from app.schemas.common import ApiModel

AttemptStatus = Literal["in_progress", "passed", "failed", "expired"]


class SurveyAnswers(ApiModel):
    """Onboarding survey: industry and specialization (first step of the mandatory path)."""

    industry: str
    specialization: str
    answers: dict[str, Any]


class AttemptStart(ApiModel):
    specialization: str
    grade: Grade


class AttemptAnswer(ApiModel):
    task_id: str
    answer: Any


class AttemptRead(ApiModel):
    id: uuid.UUID
    specialization: str
    grade: Grade
    status: AttemptStatus
    score: float | None
    started_at: datetime
    finished_at: datetime | None


class AssessmentStatus(ApiModel):
    specialization: str | None
    grade: Grade | None
    # Grade change is rate-limited (e.g. not more often than once per 3 months).
    next_grade_change_at: datetime | None
    history: list[AttemptRead]
