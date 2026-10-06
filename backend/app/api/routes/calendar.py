import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response, status
from pydantic import AwareDatetime

from app.dependencies.auth import CandidateUser, CurrentUser, EmployerUser
from app.dependencies.services import CalendarServiceDep
from app.schemas.calendar import CalendarEventRead, MeetingCreate, MeetingUpdate

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get(
    "/events",
    summary="Interviews in a range: of the company for an employer, own for a candidate",
)
async def list_events(
    user: CurrentUser,
    calendar: CalendarServiceDep,
    from_: Annotated[AwareDatetime, Query(alias="from")],
    to: AwareDatetime,
) -> list[CalendarEventRead]:
    return await calendar.events(user, from_, to)


@router.post(
    "/events",
    status_code=status.HTTP_201_CREATED,
    summary="Employer: schedule a meeting with a candidate",
    description="The candidate sees it in their calendar and confirms or declines.",
)
async def schedule_meeting(
    user: EmployerUser, data: MeetingCreate, calendar: CalendarServiceDep
) -> CalendarEventRead:
    return await calendar.schedule(user, data)


@router.put(
    "/events/{event_id}",
    summary="Employer: edit a meeting; a new time resets the candidate's answer",
)
async def reschedule_meeting(
    event_id: uuid.UUID, user: EmployerUser, data: MeetingUpdate, calendar: CalendarServiceDep
) -> CalendarEventRead:
    return await calendar.reschedule(user, event_id, data)


@router.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Employer: cancel a meeting",
)
async def cancel_meeting(
    event_id: uuid.UUID, user: EmployerUser, calendar: CalendarServiceDep
) -> Response:
    await calendar.cancel(user, event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/events/{event_id}/confirm", summary="Candidate confirms the meeting")
async def confirm_meeting(
    event_id: uuid.UUID, user: CandidateUser, calendar: CalendarServiceDep
) -> CalendarEventRead:
    return await calendar.respond(user, event_id, accept=True)


@router.post("/events/{event_id}/decline", summary="Candidate declines the meeting")
async def decline_meeting(
    event_id: uuid.UUID, user: CandidateUser, calendar: CalendarServiceDep
) -> CalendarEventRead:
    return await calendar.respond(user, event_id, accept=False)
