import uuid

from fastapi import APIRouter, status

from app.api.stub import not_implemented
from app.dependencies.auth import CandidateUser
from app.dependencies.services import AssessmentServiceDep, TestAssignmentServiceDep
from app.schemas.assessment import (
    AssessmentStatusRead,
    AssignmentRead,
    AttemptAnswer,
    AttemptDetail,
    AttemptRead,
    AttemptSignal,
    AttemptStart,
    PrimaryCategory,
    RunRequest,
    RunResponse,
    SurveyAnswers,
    TemplateRead,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("/me", summary="Categories by specialization, their cooldowns and attempt history")
async def read_status(user: CandidateUser, service: AssessmentServiceDep) -> AssessmentStatusRead:
    return await service.status(user)


@router.put("/me/primary", summary="Choose which confirmed category employers see")
async def set_primary_category(
    user: CandidateUser, data: PrimaryCategory, service: AssessmentServiceDep
) -> AssessmentStatusRead:
    return await service.set_primary(user, data.specialization)


@router.get("/templates", summary="What the grade tests consist of: time, pass score, cooldowns")
async def list_templates(_: CandidateUser, service: AssessmentServiceDep) -> list[TemplateRead]:
    return await service.templates()


@router.post("/survey", status_code=status.HTTP_204_NO_CONTENT, summary="Submit onboarding survey")
async def submit_survey(_: CandidateUser, data: SurveyAnswers) -> None:
    not_implemented("assessments.survey")


@router.post(
    "/attempts",
    status_code=status.HTTP_201_CREATED,
    summary="Start a test for the declared grade (per-candidate task variant)",
)
async def start_attempt(
    user: CandidateUser, data: AttemptStart, service: AssessmentServiceDep
) -> AttemptDetail:
    return await service.start(user, data)


@router.get("/attempts/{attempt_id}", summary="Tasks of the attempt with saved answers")
async def read_attempt(
    attempt_id: uuid.UUID, user: CandidateUser, service: AssessmentServiceDep
) -> AttemptDetail:
    return await service.read(user, attempt_id)


@router.post(
    "/attempts/{attempt_id}/answers",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Save a quiz answer or a code draft",
)
async def submit_answer(
    attempt_id: uuid.UUID, user: CandidateUser, data: AttemptAnswer, service: AssessmentServiceDep
) -> None:
    await service.answer(user, attempt_id, data)


@router.post("/attempts/{attempt_id}/run", summary="Run code on the open tests or own input")
async def run_code(
    attempt_id: uuid.UUID, user: CandidateUser, data: RunRequest, service: AssessmentServiceDep
) -> RunResponse:
    return await service.run(user, attempt_id, data)


@router.post(
    "/attempts/{attempt_id}/signals",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Report a paste or a tab switch (kept for reviewers, never scored)",
)
async def report_signal(
    attempt_id: uuid.UUID, user: CandidateUser, data: AttemptSignal, service: AssessmentServiceDep
) -> None:
    await service.signal(user, attempt_id, data)


@router.post("/attempts/{attempt_id}/finish", summary="Check hidden tests and score the attempt")
async def finish_attempt(
    attempt_id: uuid.UUID, user: CandidateUser, service: AssessmentServiceDep
) -> AttemptRead:
    return await service.finish(user, attempt_id)


@router.get("/assignments", summary="Tests companies sent to me")
async def list_assignments(
    user: CandidateUser, service: TestAssignmentServiceDep
) -> list[AssignmentRead]:
    return await service.incoming(user)


@router.post(
    "/assignments/{assignment_id}/start",
    status_code=status.HTTP_201_CREATED,
    summary="Start a test a company sent",
    description="The attempt is answered and finished through the same `/attempts` endpoints.",
)
async def start_assignment(
    assignment_id: uuid.UUID, user: CandidateUser, service: TestAssignmentServiceDep
) -> AttemptDetail:
    return await service.start(user, assignment_id)


@router.post("/assignments/{assignment_id}/decline", summary="Refuse a test a company sent")
async def decline_assignment(
    assignment_id: uuid.UUID, user: CandidateUser, service: TestAssignmentServiceDep
) -> AssignmentRead:
    return await service.decline(user, assignment_id)
