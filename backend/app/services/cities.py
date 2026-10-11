"""Resolve a typed or stored city to one GeoNames place, and copy that place onto a row."""

from collections.abc import Iterable, Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models import CandidateProfile, Vacancy
from app.models.city import City, CityAlias, CityResolutionGap
from app.repositories.city import CityRepository, normalize_city_query

# A name that matches nothing must not fall through to «no city filter».
_UNKNOWN_CITY_ID = -1
_CHOOSE = "Выберите город из списка"

# Places the tests and the demo forms use before the full dump is imported.
# Ids are the GeoNames ids, so a later import of cities1000 keeps the same rows.
REFERENCE_CITIES: tuple[tuple[int, str, str, float, float, tuple[str, ...]], ...] = (
    (524901, "Москва", "Москва", 55.75222, 37.61556, ("Moscow",)),
    (
        498817,
        "Санкт-Петербург",
        "Санкт-Петербург",
        59.93863,
        30.31413,
        ("СПб", "Питер", "Петербург", "Saint Petersburg"),
    ),
    (520555, "Нижний Новгород", "Нижегородская область", 56.32867, 44.00205, ("Nizhny Novgorod",)),
    (551487, "Казань", "Республика Татарстан", 55.78874, 49.12214, ()),
    (1489425, "Томск", "Томская область", 56.49771, 84.97437, ()),
)


async def install_reference_cities(session: AsyncSession) -> None:
    """The five places tests save. A full import replaces this set."""
    if await CityRepository(session).count():
        return
    for geoname_id, name, region, latitude, longitude, aliases in REFERENCE_CITIES:
        session.add(
            City(
                geoname_id=geoname_id,
                name=name,
                country_code="RU",
                region=region,
                latitude=latitude,
                longitude=longitude,
                feature_class="P",
                feature_code="PPL",
                population=0,
            )
        )
        session.add(
            CityAlias(
                city_id=geoname_id,
                name=name,
                norm=normalize_city_query(name),
                is_primary=True,
            )
        )
        for alias in aliases:
            session.add(
                CityAlias(
                    city_id=geoname_id,
                    name=alias,
                    norm=normalize_city_query(alias),
                    is_primary=False,
                )
            )
    await session.flush()


def choose_ids(index: dict[str, list[tuple[int, bool]]], raw: str) -> list[int]:
    """Places whose official name or an alternate name is exactly `raw`.

    When the text is the official name of some places and only an alias of others, the official
    ones win. Several official names (two «Киров») stay a list: saving must ask, a filter may
    keep every one of them.
    """
    hits = index.get(normalize_city_query(raw), [])
    primaries = [city_id for city_id, primary in hits if primary]
    chosen = primaries or [city_id for city_id, _primary in hits]
    return list(dict.fromkeys(chosen))


def ids_for_names(index: dict[str, list[tuple[int, bool]]], names: Sequence[str]) -> list[int]:
    found: list[int] = []
    for name in names:
        found.extend(choose_ids(index, name))
    unique = list(dict.fromkeys(found))
    return unique or [_UNKNOWN_CITY_ID]


class CityDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._cities = CityRepository(session)

    async def search(self, query: str, *, country_code: str, limit: int) -> list[City]:
        return await self._cities.search(query, country_code=country_code, limit=limit)

    async def require(self, city_id: int | None, text: str | None) -> City:
        """The place a form selected, or a name that is exactly one place."""
        if city_id is not None:
            city = await self._cities.get(city_id)
            if city is None:
                raise AppError(_CHOOSE)
            return city
        raw = (text or "").strip()
        if not raw:
            raise AppError(_CHOOSE)
        ids = choose_ids(await self._cities.alias_index(), raw)
        if len(ids) != 1:
            raise AppError(_CHOOSE)
        city = await self._cities.get(ids[0])
        if city is None:
            raise AppError(_CHOOSE)
        return city

    async def filter_ids(self, names: Sequence[str]) -> list[int]:
        if not names:
            return []
        return ids_for_names(await self._cities.alias_index(), names)


def place_fields(city: City | None) -> dict[str, object]:
    """Columns shared by a profile and a vacancy. `None` clears the place."""
    if city is None:
        return {
            "city": None,
            "city_id": None,
            "city_country_code": None,
            "city_region": None,
            "city_latitude": None,
            "city_longitude": None,
        }
    return {
        "city": city.name,
        "city_id": city.geoname_id,
        "city_country_code": city.country_code,
        "city_region": city.region,
        "city_latitude": city.latitude,
        "city_longitude": city.longitude,
    }


def apply_place(row: CandidateProfile | Vacancy, city: City | None) -> None:
    for name, value in place_fields(city).items():
        setattr(row, name, value)


async def bind_stored_cities(session: AsyncSession) -> list[CityResolutionGap]:
    """Point every stored city string at a GeoNames id. Unmatched rows stay, and are listed.

    The original text is not cleared: a person can still read it while the gap is open.
    """
    index = await CityRepository(session).alias_index()
    if not index:
        return []
    places = {city.geoname_id: city for city in (await session.scalars(select(City))).all()}
    await session.execute(delete(CityResolutionGap))
    gaps: list[CityResolutionGap] = []
    profiles = (await session.scalars(select(CandidateProfile))).all()
    vacancies = (await session.scalars(select(Vacancy))).all()
    gaps.extend(_bind(session, index, places, "candidate", profiles))
    gaps.extend(_bind(session, index, places, "vacancy", vacancies))
    return gaps


def _bind(
    session: AsyncSession,
    index: dict[str, list[tuple[int, bool]]],
    places: dict[int, City],
    entity: str,
    rows: Iterable[CandidateProfile | Vacancy],
) -> list[CityResolutionGap]:
    gaps: list[CityResolutionGap] = []
    for row in rows:
        raw = row.city
        if not raw or not raw.strip():
            continue
        ids = choose_ids(index, raw)
        city = places.get(ids[0]) if len(ids) == 1 else None
        if city is not None:
            apply_place(row, city)
            continue
        row.city_id = None
        gap = CityResolutionGap(entity=entity, entity_id=str(row.id), raw_value=raw.strip())
        session.add(gap)
        gaps.append(gap)
    return gaps
