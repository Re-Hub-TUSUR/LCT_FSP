from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.stub import not_implemented
from app.dependencies.auth import CurrentUser
from app.schemas.calendar import CalendarEventRead

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events", summary="Interviews, assessment slots and task deadlines in a range")
async def list_events(
    _: CurrentUser,
    from_: Annotated[datetime, Query(alias="from")],
    to: datetime,
) -> list[CalendarEventRead]:
    not_implemented("calendar.list_events")
