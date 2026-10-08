"""JSON shape of the fixture ATS. The domain package does not import this module."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FixturePerson:
    ref: str
    full_name: str
    skill_tags: tuple[str, ...]
    years: int | None
    location: str | None
    pay_wish: int | None
    cv_text: str | None


@dataclass(frozen=True, slots=True)
class FixtureOpening:
    ref: str
    label: str
    must_have: tuple[str, ...]
    pay_floor: int | None
    pay_ceiling: int | None
    place: str | None


@dataclass(frozen=True, slots=True)
class FixtureItem:
    event_id: str
    person: FixturePerson
    opening: FixtureOpening
