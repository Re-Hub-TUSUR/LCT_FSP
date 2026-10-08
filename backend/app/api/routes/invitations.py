import uuid

from fastapi import APIRouter, status

from app.dependencies.auth import CandidateUser, EmployerUser
from app.dependencies.common import PaginationDep
from app.dependencies.services import InvitationServiceDep
from app.schemas.common import Page
from app.schemas.invitation import InvitationCreate, InvitationRead

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Employer invites a specific candidate (offer + salary range)",
    description="409 while an earlier invitation of the company waits for the candidate's answer.",
)
async def create_invitation(
    user: EmployerUser, data: InvitationCreate, invitations: InvitationServiceDep
) -> InvitationRead:
    return await invitations.create(user, data)


@router.get("/incoming", summary="Candidate: invitations addressed to me, newest first")
async def list_incoming(
    user: CandidateUser, pagination: PaginationDep, invitations: InvitationServiceDep
) -> Page[InvitationRead]:
    return await invitations.incoming(user, pagination)


@router.get("/outgoing", summary="Employer: invitations sent by my company, newest first")
async def list_outgoing(
    user: EmployerUser, pagination: PaginationDep, invitations: InvitationServiceDep
) -> Page[InvitationRead]:
    return await invitations.outgoing(user, pagination)


@router.post("/{invitation_id}/accept", summary="Candidate accepts — contacts are revealed")
async def accept_invitation(
    invitation_id: uuid.UUID, user: CandidateUser, invitations: InvitationServiceDep
) -> InvitationRead:
    return await invitations.respond(user, invitation_id, accept=True)


@router.post("/{invitation_id}/decline", summary="Candidate declines")
async def decline_invitation(
    invitation_id: uuid.UUID, user: CandidateUser, invitations: InvitationServiceDep
) -> InvitationRead:
    return await invitations.respond(user, invitation_id, accept=False)
