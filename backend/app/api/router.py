from fastapi import APIRouter

from app.api.routes import (
    admin,
    applications,
    assessments,
    auth,
    calendar,
    candidates,
    categories,
    companies,
    health,
    invitations,
    matching,
    test_assignments,
    users,
    vacancies,
)
from app.schemas.common import ERROR_RESPONSES

API_PREFIX = "/api/v1"

api_router = APIRouter(prefix=API_PREFIX, responses=ERROR_RESPONSES)

for module in (
    health,
    auth,
    users,
    categories,
    candidates,
    companies,
    test_assignments,
    vacancies,
    invitations,
    applications,
    matching,
    calendar,
    assessments,
    admin,
):
    api_router.include_router(module.router)
