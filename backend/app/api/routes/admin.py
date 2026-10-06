from fastapi import APIRouter

from app.api.routes.assessment_bank import bank_router
from app.dependencies.auth import AdminUser
from app.dependencies.common import PaginationDep
from app.dependencies.services import UserRepositoryDep
from app.schemas.common import Page
from app.schemas.user import UserRead

router = APIRouter(prefix="/admin", tags=["admin"])
# Platform task bank and grade test templates.
router.include_router(bank_router(AdminUser))


@router.get("/users", summary="All accounts (admin only)")
async def list_users(
    _: AdminUser, pagination: PaginationDep, users: UserRepositoryDep
) -> Page[UserRead]:
    items, total = await users.list(limit=pagination.limit, offset=pagination.offset)
    return Page[UserRead].build(
        [UserRead.model_validate(user) for user in items],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
    )
