from app.schemas.common import ApiModel


class CityHit(ApiModel):
    """One populated place a form can select."""

    id: int
    name: str
    country_code: str
    region: str | None
    latitude: float
    longitude: float
