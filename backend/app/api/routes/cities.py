from typing import Annotated

from fastapi import APIRouter, Query

from app.dependencies.common import SessionDep
from app.schemas.city import CityHit
from app.services.cities import CityDirectory

router = APIRouter(prefix="/cities", tags=["cities"])

# The form shows at most this many suggestions.
_MAX_HINTS = 10


@router.get("/search", summary="Cities from the GeoNames dictionary")
async def search_cities(
    session: SessionDep,
    q: Annotated[str, Query(max_length=100)],
    country_code: Annotated[str, Query(alias="countryCode", min_length=2, max_length=2)] = "RU",
    limit: Annotated[int, Query(ge=1, le=_MAX_HINTS)] = _MAX_HINTS,
) -> list[CityHit]:
    """Prefix, substring and alternate names. «г.» and «гор.» are ignored. Case does not matter."""
    rows = await CityDirectory(session).search(q, country_code=country_code.upper(), limit=limit)
    return [
        CityHit(
            id=city.geoname_id,
            name=city.name,
            country_code=city.country_code,
            region=city.region,
            latitude=city.latitude,
            longitude=city.longitude,
        )
        for city in rows
    ]
