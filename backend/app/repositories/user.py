import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class UserRepository:
    """Persistence of user accounts. No business rules here — only queries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_yandex_id(self, yandex_id: str) -> User | None:
        result = await self._session.execute(select(User).where(User.yandex_id == yandex_id))
        return result.scalar_one_or_none()

    async def pending_photo(self, user_id: uuid.UUID) -> tuple[bytes, str] | None:
        row = (
            await self._session.execute(
                select(User.pending_photo, User.pending_photo_type).where(User.id == user_id)
            )
        ).one_or_none()
        if row is None or row[0] is None or not row[1]:
            return None
        return bytes(row[0]), row[1]

    def clear_pending_photo(self, user: User) -> None:
        user.pending_photo = None
        user.pending_photo_type = None

    async def add(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def list(self, *, limit: int, offset: int) -> tuple[Sequence[User], int]:
        total = await self._session.scalar(select(func.count()).select_from(User))
        result = await self._session.execute(
            select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all(), total or 0
