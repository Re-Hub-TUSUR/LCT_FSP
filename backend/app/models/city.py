"""Populated places from GeoNames. A resume or a vacancy stores the geoname id, not free text."""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class City(Base):
    """One populated place. `geoname_id` is the GeoNames id."""

    __tablename__ = "cities"

    geoname_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(200))
    country_code: Mapped[str] = mapped_column(String(2), index=True)
    region: Mapped[str | None] = mapped_column(String(200))
    latitude: Mapped[float]
    longitude: Mapped[float]
    feature_class: Mapped[str] = mapped_column(String(1))
    feature_code: Mapped[str] = mapped_column(String(10))
    population: Mapped[int] = mapped_column(Integer, default=0)
    aliases: Mapped[list["CityAlias"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )


class CityAlias(Base):
    """A name the search matches: the official one and the alternate names."""

    __tablename__ = "city_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(
        ForeignKey("cities.geoname_id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    # Folded for search: lower case, «ё» as «е», without «г.» / «гор.».
    norm: Mapped[str] = mapped_column(String(200), index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)


class CityResolutionGap(Base):
    """A free-text city that the dictionary could not match. Kept for a person to fix."""

    __tablename__ = "city_resolution_gaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity: Mapped[str] = mapped_column(String(32))
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    raw_value: Mapped[str] = mapped_column(Text)
