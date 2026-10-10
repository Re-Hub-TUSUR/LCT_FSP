from fastapi import APIRouter
from fastapi.responses import Response

from app.core.errors import NotFoundError
from app.dependencies.auth import CurrentUser
from app.dependencies.services import UserRepositoryDep
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", summary="Current account")
async def read_me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.get("/me/pending-photo", summary="Portrait staged by Yandex ID, before the resume exists")
async def read_pending_photo(user: CurrentUser, users: UserRepositoryDep) -> Response:
    if not user.pending_photo_type:
        raise NotFoundError("Фото не загружено")
    found = await users.pending_photo(user.id)
    if found is None:
        raise NotFoundError("Фото не загружено")
    body, media = found
    return Response(
        content=body,
        media_type=media,
        headers={
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": "inline",
            "Cache-Control": "private, no-store",
        },
    )


@router.patch("/me", summary="Name and phone of the account owner")
async def update_me(user: CurrentUser, data: UserUpdate) -> UserRead:
    user.first_name = data.first_name.strip()
    user.last_name = data.last_name.strip()
    phone = data.phone.strip() if data.phone else ""
    user.phone = phone or None
    return UserRead.model_validate(user)
