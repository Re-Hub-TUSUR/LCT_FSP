from fastapi import APIRouter, status

from app.dependencies.auth import EmployerUser
from app.dependencies.services import AtsServiceDep
from app.schemas.ats import AtsApplicationRead, AtsConnectionRead, AtsPollRead

router = APIRouter(prefix="/ats", tags=["ats"])


@router.get("/connection", summary="Whether this employer polls an ATS")
async def read_connection(user: EmployerUser, ats: AtsServiceDep) -> AtsConnectionRead:
    return await ats.read_connection(user)


@router.post(
    "/connection",
    status_code=status.HTTP_201_CREATED,
    summary="Link the company to the configured ATS provider",
)
async def connect(user: EmployerUser, ats: AtsServiceDep) -> AtsConnectionRead:
    return await ats.connect(user)


@router.post("/poll", summary="Pull new applications and screen the ones not seen before")
async def poll(user: EmployerUser, ats: AtsServiceDep) -> AtsPollRead:
    return await ats.poll(user)


@router.get("/applications", summary="External applications and the latest screening")
async def list_applications(user: EmployerUser, ats: AtsServiceDep) -> list[AtsApplicationRead]:
    return await ats.list_applications(user)
