from fastapi import APIRouter

from app.dependencies.auth import CurrentUser
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", summary="Current account")
async def read_me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
