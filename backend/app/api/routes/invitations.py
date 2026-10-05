import uuid

from fastapi import APIRouter, status

from app.api.stub import not_implemented
from app.dependencies.auth import CandidateUser, EmployerUser
from app.dependencies.common import PaginationDep
from app.schemas.common import Page
from app.schemas.invitation import InvitationCreate, InvitationRead

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Employer invites a specific candidate (offer + salary range)",
)
async def create_invitation(_: EmployerUser, data: InvitationCreate) -> InvitationRead:
    not_implemented("invitations.create")


@router.get("/incoming", summary="Candidate: invitations addressed to me")
async def list_incoming(_: CandidateUser, pagination: PaginationDep) -> Page[InvitationRead]:
    not_implemented("invitations.list_incoming")


@router.get("/outgoing", summary="Employer: invitations sent by my company")
async def list_outgoing(_: EmployerUser, pagination: PaginationDep) -> Page[InvitationRead]:
    not_implemented("invitations.list_outgoing")


@router.post("/{invitation_id}/accept", summary="Candidate accepts — contacts are revealed")
async def accept_invitation(invitation_id: uuid.UUID, _: CandidateUser) -> InvitationRead:
    not_implemented("invitations.accept")


@router.post("/{invitation_id}/decline", summary="Candidate declines")
async def decline_invitation(invitation_id: uuid.UUID, _: CandidateUser) -> InvitationRead:
    not_implemented("invitations.decline")
