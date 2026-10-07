from fastapi import APIRouter

from app.dependencies.auth import CurrentUser
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", summary="Current account")
async def read_me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", summary="Name and phone of the account owner")
async def update_me(user: CurrentUser, data: UserUpdate) -> UserRead:
    user.first_name = data.first_name.strip()
    user.last_name = data.last_name.strip()
    phone = data.phone.strip() if data.phone else ""
    user.phone = phone or None
    return UserRead.model_validate(user)
