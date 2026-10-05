import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.stub import not_implemented
from app.dependencies.auth import EmployerUser
from app.schemas.matching import HiringNeedCreate, HiringNeedRead, RecommendationList

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post(
    "/needs", status_code=status.HTTP_201_CREATED, summary="Describe a hiring need (stack, grade)"
)
async def create_need(_: EmployerUser, data: HiringNeedCreate) -> HiringNeedRead:
    not_implemented("matching.create_need")


@router.get("/recommendations", summary="Explained, ranked selection of candidates")
async def recommendations(
    _: EmployerUser,
    need_id: Annotated[uuid.UUID | None, Query(alias="needId")] = None,
) -> RecommendationList:
    not_implemented("matching.recommendations")
