from fastapi import APIRouter

from app.admin import company_documents
from app.api.routes import (
    admin,
    applications,
    assessments,
    auth,
    calendar,
    candidates,
    categories,
    companies,
    conversations,
    health,
    invitations,
    matching,
    notifications,
    responses,
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
    company_documents,
    test_assignments,
    vacancies,
    invitations,
    applications,
    matching,
    calendar,
    responses,
    conversations,
    notifications,
    assessments,
    admin,
):
    api_router.include_router(module.router)
