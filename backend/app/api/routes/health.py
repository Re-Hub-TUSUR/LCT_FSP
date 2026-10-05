import logging
from typing import Literal

from fastapi import APIRouter
from sqlalchemy import text

from app.core.errors import ServiceUnavailableError
from app.dependencies.common import SessionDep
from app.schemas.common import ApiModel, ErrorResponse

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


class HealthStatus(ApiModel):
    status: Literal["ok"]


@router.get("", summary="Liveness probe")
async def live() -> HealthStatus:
    return HealthStatus(status="ok")


@router.get(
    "/ready",
    summary="Readiness probe (checks the database)",
    responses={503: {"model": ErrorResponse}},
)
async def ready(session: SessionDep) -> HealthStatus:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("Database is not reachable")
        raise ServiceUnavailableError("База данных недоступна") from exc
    return HealthStatus(status="ok")
