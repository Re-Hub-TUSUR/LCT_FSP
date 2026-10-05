import uuid

from fastapi import APIRouter, status

from app.api.stub import not_implemented
from app.dependencies.auth import CandidateUser
from app.schemas.assessment import (
    AssessmentStatus,
    AttemptAnswer,
    AttemptRead,
    AttemptStart,
    SurveyAnswers,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("/me", summary="Current category, grade-change cooldown and attempt history")
async def read_status(_: CandidateUser) -> AssessmentStatus:
    not_implemented("assessments.status")


@router.post("/survey", status_code=status.HTTP_204_NO_CONTENT, summary="Submit onboarding survey")
async def submit_survey(_: CandidateUser, data: SurveyAnswers) -> None:
    not_implemented("assessments.survey")


@router.post(
    "/attempts",
    status_code=status.HTTP_201_CREATED,
    summary="Start a test for the declared grade (per-candidate task variant)",
)
async def start_attempt(_: CandidateUser, data: AttemptStart) -> AttemptRead:
    not_implemented("assessments.start_attempt")


@router.post("/attempts/{attempt_id}/answers", summary="Submit an answer within an attempt")
async def submit_answer(
    attempt_id: uuid.UUID, _: CandidateUser, data: AttemptAnswer
) -> AttemptRead:
    not_implemented("assessments.submit_answer")


@router.post("/attempts/{attempt_id}/finish", summary="Finish and score the attempt")
async def finish_attempt(attempt_id: uuid.UUID, _: CandidateUser) -> AttemptRead:
    not_implemented("assessments.finish_attempt")
