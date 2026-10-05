from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import session_scope

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20
# page × perPage stays within Elasticsearch's default result window (10 000 hits).
MAX_PAGE = 100


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async for session in session_scope():
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@dataclass(frozen=True, slots=True)
class Pagination:
    page: int
    per_page: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        return self.per_page


def get_pagination(
    page: Annotated[int, Query(ge=1, le=MAX_PAGE, description="Номер страницы, с 1")] = 1,
    per_page: Annotated[
        int, Query(alias="perPage", ge=1, le=MAX_PAGE_SIZE, description="Элементов на странице")
    ] = DEFAULT_PAGE_SIZE,
) -> Pagination:
    return Pagination(page=page, per_page=per_page)


PaginationDep = Annotated[Pagination, Depends(get_pagination)]
