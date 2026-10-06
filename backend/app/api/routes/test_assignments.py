"""Employer side of test assignments. The candidate side lives next to the attempts."""

import uuid

from fastapi import APIRouter, Response, status

from app.dependencies.auth import EmployerUser
from app.dependencies.services import TestAssignmentServiceDep
from app.schemas.assessment import (
    AssignmentCreate,
    AssignmentDetail,
    AssignmentRead,
    ReviewRequest,
)

router = APIRouter(prefix="/companies/me/test-assignments", tags=["companies"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Send one of the company's tests to a matched candidate",
    description=(
        "Allowed after a match: the recruiter liked the candidate and the candidate liked a "
        "vacancy of the company. Otherwise 409."
    ),
)
async def send_assignment(
    user: EmployerUser, data: AssignmentCreate, service: TestAssignmentServiceDep
) -> AssignmentRead:
    return await service.send(user, data)


@router.get("", summary="Tests the company sent, newest first")
async def list_assignments(
    user: EmployerUser, service: TestAssignmentServiceDep
) -> list[AssignmentRead]:
    return await service.outgoing(user)


@router.get(
    "/{assignment_id}",
    summary="A taken test: answers, points and anti-cheat signals",
    description="Answers appear once the candidate finished; a running attempt shows nothing.",
)
async def read_assignment(
    assignment_id: uuid.UUID, user: EmployerUser, service: TestAssignmentServiceDep
) -> AssignmentDetail:
    return await service.detail(user, assignment_id)


@router.put(
    "/{assignment_id}/review",
    summary="Grade hand-checked answers; the score appears when none is left ungraded",
)
async def review_assignment(
    assignment_id: uuid.UUID,
    user: EmployerUser,
    data: ReviewRequest,
    service: TestAssignmentServiceDep,
) -> AssignmentDetail:
    return await service.review(user, assignment_id, data)


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Take back a test the candidate has not started",
)
async def revoke_assignment(
    assignment_id: uuid.UUID, user: EmployerUser, service: TestAssignmentServiceDep
) -> Response:
    await service.revoke(user, assignment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
