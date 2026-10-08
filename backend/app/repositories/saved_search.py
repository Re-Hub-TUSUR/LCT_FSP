import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SavedSearch
from app.models.enums import SavedSearchKind


class SavedSearchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def for_user(self, user_id: uuid.UUID, kind: SavedSearchKind) -> Sequence[SavedSearch]:
        """A user's searches, the newest first."""
        result = await self._session.scalars(
            select(SavedSearch)
            .where(SavedSearch.user_id == user_id, SavedSearch.kind == kind)
            .order_by(SavedSearch.created_at.desc(), SavedSearch.id)
        )
        return result.all()

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        total = await self._session.scalar(
            select(func.count()).select_from(SavedSearch).where(SavedSearch.user_id == user_id)
        )
        return total or 0

    async def get(self, search_id: uuid.UUID) -> SavedSearch | None:
        return await self._session.get(SavedSearch, search_id)

    async def all(self) -> Sequence[SavedSearch]:
        """Every saved search, grouped by user: the alerts check them one user at a time."""
        result = await self._session.scalars(
            select(SavedSearch).order_by(SavedSearch.user_id, SavedSearch.created_at)
        )
        return result.all()

    async def add(self, search: SavedSearch) -> SavedSearch:
        self._session.add(search)
        await self._session.flush()
        return search

    async def delete(self, search: SavedSearch) -> None:
        await self._session.delete(search)
        await self._session.flush()
