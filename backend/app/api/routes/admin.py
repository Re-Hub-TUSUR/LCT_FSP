from fastapi import APIRouter

from app.dependencies.auth import AdminUser
from app.dependencies.common import PaginationDep
from app.dependencies.services import UserRepositoryDep
from app.schemas.common import Page
from app.schemas.user import UserRead

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", summary="All accounts (admin only)")
async def list_users(
    _: AdminUser, pagination: PaginationDep, users: UserRepositoryDep
) -> Page[UserRead]:
    items, total = await users.list(limit=pagination.limit, offset=pagination.offset)
    return Page[UserRead](
        items=[UserRead.model_validate(user) for user in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
