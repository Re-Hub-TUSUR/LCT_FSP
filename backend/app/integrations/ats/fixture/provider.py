"""Second ATS, fed by a JSON file, so the contract is proven without a live vendor."""

import json
from importlib.resources import files

from app.integrations.ats.fixture.dto import FixtureOpening, FixturePerson
from app.integrations.ats.normalized import (
    AtsRecord,
    NormalizedApplication,
    NormalizedCandidate,
    NormalizedJob,
    PollChange,
    PollPage,
)


class FixtureAtsProvider:
    name = "fixture"

    def __init__(self, items: tuple[PollChange, ...] | None = None) -> None:
        self._items = items if items is not None else _load()
        self._written: dict[str, list[AtsRecord]] = {}

    async def poll(self, cursor: str | None) -> PollPage:
        start = _cursor_index(cursor, len(self._items))
        return PollPage(changes=self._items[start:], next_cursor=str(len(self._items)))

    async def write_tag(self, external_application_id: str, tag: str) -> None:
        self._remember(external_application_id, AtsRecord(kind="tag", value=tag))

    async def write_note(self, external_application_id: str, note: str) -> None:
        self._remember(external_application_id, AtsRecord(kind="note", value=note))

    async def write_score(self, external_application_id: str, score: int) -> None:
        self._remember(external_application_id, AtsRecord(kind="score", value=str(score)))

    def records(self, external_application_id: str) -> tuple[AtsRecord, ...]:
        return tuple(self._written.get(external_application_id, ()))

    def _remember(self, external_application_id: str, record: AtsRecord) -> None:
        self._written.setdefault(external_application_id, []).append(record)


def _load() -> tuple[PollChange, ...]:
    payload = files("app.integrations.ats.fixture").joinpath("payloads.json").read_text("utf-8")
    raw = json.loads(payload)
    items = raw["items"]
    if not isinstance(items, list):
        return ()
    return tuple(_change(item) for item in items if isinstance(item, dict))


def _change(item: dict[str, object]) -> PollChange:
    person = _person(item.get("person"))
    opening = _opening(item.get("opening"))
    event_id = _text(item.get("eventId")) or person.ref
    return PollChange(
        external_event_id=event_id,
        raw=item,
        application=NormalizedApplication(
            external_id=event_id,
            candidate=NormalizedCandidate(
                external_id=person.ref,
                name=person.full_name,
                skills=person.skill_tags,
                experience_years=person.years,
                city=person.location,
                salary_expectation=person.pay_wish,
                resume_text=person.cv_text,
            ),
            job=NormalizedJob(
                external_id=opening.ref,
                title=opening.label,
                required_skills=opening.must_have,
                salary_from=opening.pay_floor,
                salary_to=opening.pay_ceiling,
                city=opening.place,
            ),
        ),
    )


def _person(value: object) -> FixturePerson:
    data = value if isinstance(value, dict) else {}
    return FixturePerson(
        ref=_text(data.get("ref")) or "person",
        full_name=_text(data.get("fullName")) or "Без имени",
        skill_tags=_strings(data.get("skillTags")),
        years=_whole(data.get("years")),
        location=_text(data.get("location")),
        pay_wish=_whole(data.get("payWish")),
        cv_text=_text(data.get("cvText")),
    )


def _opening(value: object) -> FixtureOpening:
    data = value if isinstance(value, dict) else {}
    return FixtureOpening(
        ref=_text(data.get("ref")) or "opening",
        label=_text(data.get("label")) or "Вакансия",
        must_have=_strings(data.get("mustHave")),
        pay_floor=_whole(data.get("payFloor")),
        pay_ceiling=_whole(data.get("payCeiling")),
        place=_text(data.get("place")),
    )


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.split())
    return text or None


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(text for item in value if (text := _text(item)))


def _whole(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _cursor_index(cursor: str | None, length: int) -> int:
    if not cursor:
        return 0
    try:
        index = int(cursor)
    except ValueError:
        return 0
    return max(0, min(index, length))
