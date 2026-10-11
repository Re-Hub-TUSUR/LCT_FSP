"""Reads of the GeoNames city dictionary."""

import re
from collections import defaultdict

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City, CityAlias

# «г. Москва», «гор. Казань», «город Нижний Новгород» are the same place as the bare name.
_PREFIX = re.compile(r"^(?:город|гор|г)(?:\.\s*|\s+)", re.IGNORECASE)
_SPACES = re.compile(r"\s+")
_LIKE_ESCAPE = str.maketrans({"\\": "\\\\", "%": "\\%", "_": "\\_"})
_MIN_QUERY = 2


def normalize_city_query(value: str) -> str:
    """Fold a typed city the way aliases are stored: case, «ё», and a leading «г.» / «гор.»."""
    text = value.strip().replace("ё", "е").replace("Ё", "е")
    text = _PREFIX.sub("", text)
    return _SPACES.sub(" ", text).strip(" .,;").casefold()


def _like(fragment: str) -> str:
    return fragment.translate(_LIKE_ESCAPE)


class CityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, geoname_id: int) -> City | None:
        return await self._session.get(City, geoname_id)

    async def search(self, query: str, *, country_code: str, limit: int) -> list[City]:
        """Prefix matches first, then a substring, official names before alternate ones."""
        norm = normalize_city_query(query)
        if len(norm) < _MIN_QUERY:
            return []
        prefix = f"{_like(norm)}%"
        contains = f"%{_like(norm)}%"
        rank = case(
            (and_(CityAlias.is_primary.is_(True), CityAlias.norm == norm), 0),
            (and_(CityAlias.is_primary.is_(True), CityAlias.norm.like(prefix, escape="\\")), 1),
            (and_(CityAlias.is_primary.is_(True), CityAlias.norm.like(contains, escape="\\")), 2),
            (CityAlias.norm == norm, 3),
            (CityAlias.norm.like(prefix, escape="\\"), 4),
            else_=5,
        )
        scored = (
            select(CityAlias.city_id.label("city_id"), func.min(rank).label("rank"))
            .where(CityAlias.norm.like(contains, escape="\\"))
            .group_by(CityAlias.city_id)
            .subquery()
        )
        rows = await self._session.scalars(
            select(City)
            .join(scored, scored.c.city_id == City.geoname_id)
            .where(City.country_code == country_code)
            .order_by(scored.c.rank, City.population.desc(), City.name)
            .limit(limit)
        )
        return list(rows)

    async def alias_index(self) -> dict[str, list[tuple[int, bool]]]:
        """`norm` → (geoname id, whether that name is the official one)."""
        rows = await self._session.execute(
            select(CityAlias.norm, CityAlias.city_id, CityAlias.is_primary)
        )
        index: dict[str, list[tuple[int, bool]]] = defaultdict(list)
        for norm, city_id, primary in rows:
            index[norm].append((city_id, primary))
        return index

    async def count(self) -> int:
        return int(await self._session.scalar(select(func.count()).select_from(City)) or 0)
