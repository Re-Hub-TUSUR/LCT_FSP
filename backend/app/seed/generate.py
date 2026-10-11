"""Deterministic generator of the demo dataset in `app/seed/data/`.

Run `uv run python -m app.seed.generate` to rewrite the JSON files. They are committed, and
`tests/test_seed.py` checks that they match this generator: change `content.py` and regenerate
instead of editing the JSON by hand.

Dates are stored as "days ago" and resolved when the data is loaded, so the demo never looks stale.
"""

import json
import random
import uuid
import zlib
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from app.models import Vacancy
from app.models.enums import (
    FspDiscipline,
    FspEventKind,
    FspEventLevel,
    FspOutcome,
    FspParticipation,
    FspTitleKind,
    Grade,
    JobStatus,
    WorkFormat,
)
from app.search.filters import FilterFacts, failed_groups, fsp_marks, passes
from app.seed import content
from app.seed.content import CompanyPlan, Track, VacancyPlan
from app.seed.details import candidate_details, vacancy_details
from app.seed.fixtures import DATA_DIR, CandidateFixture, VacancyFixture
from app.services.candidate_search import candidate_query, vacancy_filters
from app.services.matching import normalize_term

SEED: Final = 20261006
EMAIL_DOMAIN: Final = "example.com"

# The demo candidate is the first record: python-backend, middle, Moscow, with FSP results.
DEMO_CANDIDATE_EMAIL: Final = "candidate@example.com"
DEMO_EMPLOYER_EMAIL: Final = "employer@example.com"
DEMO_EMPLOYER2_EMAIL: Final = "employer2@example.com"
DEMO_EMPLOYER_EMAILS: Final = (DEMO_EMPLOYER_EMAIL, DEMO_EMPLOYER2_EMAIL)
DEMO_TRACK: Final = "python-backend"

HIDDEN_CANDIDATES: Final = 4
UNTESTED_CANDIDATES: Final = 12
# Selecting any vacancy fills its filters; that search must still find this many people.
MATCHES_PER_VACANCY: Final = 10
# Every N-th candidate with an FSP ID has no results yet (linked, but nothing to show).
FSP_LINKED_WITHOUT_RESULTS_EVERY: Final = 12

CURRENT_YEAR: Final = 2026
FIRST_FSP_YEAR: Final = 2022

EXPERIENCE_YEARS: Final[dict[Grade, tuple[int, int]]] = {
    Grade.INTERN: (0, 1),
    Grade.JUNIOR: (0, 2),
    Grade.MIDDLE: (2, 5),
    Grade.SENIOR: (4, 9),
    Grade.LEAD: (6, 14),
}

# How many technologies besides the track core a resume / a vacancy lists.
RESUME_EXTRA_STACK: Final[dict[Grade, tuple[int, int]]] = {
    Grade.INTERN: (2, 3),
    Grade.JUNIOR: (3, 4),
    Grade.MIDDLE: (4, 6),
    Grade.SENIOR: (5, 7),
    Grade.LEAD: (5, 7),
}
VACANCY_EXTRA_STACK: Final[dict[Grade, int]] = {
    Grade.INTERN: 2,
    Grade.JUNIOR: 3,
    Grade.MIDDLE: 4,
    Grade.SENIOR: 5,
    Grade.LEAD: 5,
}

GRADE_PREFIX: Final[dict[Grade, str]] = {
    Grade.INTERN: "Стажёр",
    Grade.JUNIOR: "Junior",
    Grade.MIDDLE: "Middle",
    Grade.SENIOR: "Senior",
}

TRANSLIT: Final[dict[str, str]] = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}

Record = dict[str, Any]


@dataclass(slots=True)
class _Registry:
    """Values that must stay unique across the dataset."""

    names: set[str] = field(default_factory=set)
    emails: set[str] = field(default_factory=set)
    handles: set[str] = field(default_factory=set)
    fsp_ids: set[str] = field(default_factory=set)
    fsp_linked: int = 0


@dataclass(frozen=True, slots=True)
class _Person:
    first: str
    last: str
    female: bool

    def pick(self, male: str, female: str) -> str:
        return female if self.female else male


def translit(text: str) -> str:
    return "".join(TRANSLIT.get(char, char) for char in text.lower())


def feminine_surname(surname: str) -> str:
    if surname.endswith(("ский", "цкий")):
        return surname[:-2] + "ая"
    if surname.endswith(("ов", "ев", "ёв", "ин", "ын")):
        return surname + "а"
    return surname


def years_word(count: int) -> str:
    """Russian plural of «год» for a number: 1 год, 3 года, 5 лет, 21 год."""
    if count % 10 == 1 and count % 100 != 11:  # noqa: PLR2004
        return "год"
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:  # noqa: PLR2004
        return "года"
    return "лет"


def round_salary(value: float) -> int:
    step = 5_000 if value < 150_000 else 10_000  # noqa: PLR2004
    return max(step, round(value / step) * step)


def _weighted[T](rng: random.Random, options: Sequence[tuple[T, float]]) -> T:
    values = [value for value, _ in options]
    weights = [weight for _, weight in options]
    return rng.choices(values, weights=weights)[0]


def _join(items: Sequence[str]) -> str:
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} и {items[-1]}"


def _bullets(items: Sequence[str]) -> str:
    return "\n".join(
        f"— {item}{'.' if index == len(items) - 1 else ';'}" for index, item in enumerate(items)
    )


def _allocate_grades(count: int) -> list[Grade]:
    """Largest-remainder split of `count` people by `GRADE_SHARES`."""
    exact = {grade: share * count for grade, share in content.GRADE_SHARES.items()}
    sizes = {grade: int(value) for grade, value in exact.items()}
    by_remainder = sorted(exact, key=lambda grade: exact[grade] - sizes[grade], reverse=True)
    for grade in by_remainder[: count - sum(sizes.values())]:
        sizes[grade] += 1
    return [grade for grade, size in sizes.items() for _ in range(size)]


def _candidate_plan(rng: random.Random) -> list[tuple[Track, Grade]]:
    by_specialization: dict[str, list[Track]] = {}
    for key, size in content.CANDIDATES_PER_TRACK.items():
        track = content.TRACKS_BY_KEY[key]
        by_specialization.setdefault(track.specialization, []).extend([track] * size)

    plan: list[tuple[Track, Grade]] = []
    for tracks in by_specialization.values():
        grades = _allocate_grades(len(tracks))
        rng.shuffle(grades)
        plan.extend(zip(tracks, grades, strict=True))
    rng.shuffle(plan)

    demo = next(
        index
        for index, (track, grade) in enumerate(plan)
        if track.key == DEMO_TRACK and grade == Grade.MIDDLE
    )
    plan.insert(0, plan.pop(demo))
    return plan


def _person(rng: random.Random, track: Track, registry: _Registry) -> _Person:
    while True:
        female = rng.random() < track.female_share
        first = rng.choice(content.FEMALE_NAMES if female else content.MALE_NAMES)
        surname = rng.choice(content.SURNAMES)
        last = feminine_surname(surname) if female else surname
        if f"{first} {last}" not in registry.names:
            registry.names.add(f"{first} {last}")
            return _Person(first, last, female)


def _email(person: _Person, registry: _Registry) -> str:
    base = f"{translit(person.first)[0]}.{translit(person.last)}"
    email, suffix = f"{base}@{EMAIL_DOMAIN}", 2
    while email in registry.emails:
        email, suffix = f"{base}{suffix}@{EMAIL_DOMAIN}", suffix + 1
    registry.emails.add(email)
    return email


def _telegram(rng: random.Random, person: _Person, registry: _Registry) -> str:
    while True:
        handle = f"@{translit(person.first)[0]}{translit(person.last)}_{rng.randint(100, 999)}"
        if handle not in registry.handles:
            registry.handles.add(handle)
            return handle


def _phone(rng: random.Random) -> str:
    return (
        f"+7 9{rng.randint(10, 99)} {rng.randint(100, 999)}-"
        f"{rng.randint(10, 99)}-{rng.randint(10, 99)}"
    )


def _fsp_member_id(rng: random.Random, registry: _Registry) -> str:
    while True:
        member_id = f"FSP-{rng.randint(100_000, 999_999)}"
        if member_id not in registry.fsp_ids:
            registry.fsp_ids.add(member_id)
            return member_id


def _headline(rng: random.Random, track: Track, grade: Grade) -> str:
    if grade == Grade.LEAD:
        return rng.choice(track.lead_titles)
    title = rng.choice(track.titles)
    # "Senior аналитик данных", but "Senior Data Scientist" / "Senior QA-инженер".
    if not title[0].isascii() and title[0].isupper() and title[1].islower():
        title = title[0].lower() + title[1:]
    return f"{GRADE_PREFIX[grade]} {title}"


def _stack(rng: random.Random, core: Sequence[str], extra: Sequence[str], size: int) -> list[str]:
    return [*core, *rng.sample(list(extra), min(size, len(extra)))]


def _salary_expectation(
    rng: random.Random, track: Track, grade: Grade, years: int, city: content.City
) -> int:
    seniority = 1 + 0.04 * (years - EXPERIENCE_YEARS[grade][0])
    value = (
        content.GRADE_SALARY[grade]
        * content.SPECIALIZATION_SALARY_FACTOR[track.specialization]
        * city.salary_factor
        * seniority
        * rng.uniform(0.88, 1.15)
    )
    return round_salary(value)


def _place(rng: random.Random, level: FspEventLevel) -> int | None:
    roll = rng.random()
    if level == FspEventLevel.NATIONAL:
        thresholds, finalists = (0.06, 0.14, 0.24, 0.6), (4, 15)
    else:
        thresholds, finalists = (0.18, 0.36, 0.52, 0.75), (4, 10)
    for place, threshold in enumerate(thresholds[:3], start=1):
        if roll < threshold:
            return place
    if roll < thresholds[3]:
        return rng.randint(*finalists)
    return None


def _achievements(
    rng: random.Random, track: Track, grade: Grade, years: int, city: content.City
) -> list[Record]:
    count = _weighted(rng, ((1, 40), (2, 30), (3, 20), (4, 10)))
    first_year = max(FIRST_FSP_YEAR, CURRENT_YEAR - years - 2)
    results: list[Record] = []
    seen: set[tuple[str, int, str]] = set()
    while len(results) < count:
        discipline = _weighted(rng, track.fsp)
        year = rng.randint(first_year, CURRENT_YEAR)
        level = _weighted(rng, ((FspEventLevel.NATIONAL, 45), (FspEventLevel.REGIONAL, 55)))
        if level == FspEventLevel.NATIONAL:
            youth = grade == Grade.INTERN and year < CURRENT_YEAR and rng.random() < 0.3  # noqa: PLR2004
            event = content.FSP_YOUTH_EVENT if youth else rng.choice(content.FSP_NATIONAL_EVENTS)
        else:
            event = rng.choice(content.FSP_REGIONAL_EVENTS).format(region=city.region)
        if (event, year, discipline) in seen:
            continue
        seen.add((event, year, discipline))
        results.append(
            {
                "event_name": event,
                "discipline": discipline.value,
                "level": level.value,
                "year": year,
                "place": _place(rng, level),
            }
        )
    results.sort(key=lambda item: (-item["year"], item["place"] or 99))
    return results


def _registry_id(prefix: str, key: str, index: int) -> str:
    return f"{prefix}-{zlib.crc32(f'{key}:{index}'.encode()):08x}"


def _event_kind(event_name: str) -> FspEventKind:
    if event_name.startswith("Кубок"):
        return FspEventKind.CUP
    return FspEventKind.CHAMPIONSHIP


def _registry_fields(key: str, achievements: Sequence[Record]) -> tuple[list[Record], list[Record]]:
    """What the FSP registry adds to a result: its id, event kind, team, and the sport title.

    A separate generator seeded by the candidate key: the main sequence, and with it the rest of
    the dataset, does not depend on these fields.
    """
    rng = random.Random(f"fsp:{key}")  # noqa: S311 - reproducible fake data
    results: list[Record] = []
    for index, item in enumerate(achievements):
        discipline = FspDiscipline(item["discipline"])
        event_name = item["event_name"]
        kind = _event_kind(event_name)
        national = item["level"] == FspEventLevel.NATIONAL.value
        hackathons = content.FSP_HACKATHON_EVENTS.get(discipline)
        if national and hackathons:
            if rng.random() < 0.4:  # noqa: PLR2004
                event_name, kind = rng.choice(hackathons), FspEventKind.HACKATHON
        elif national and discipline == FspDiscipline.ALGORITHMIC and rng.random() < 0.2:  # noqa: PLR2004
            event_name, kind = content.FSP_OLYMPIAD_EVENT, FspEventKind.OLYMPIAD
        team = kind == FspEventKind.HACKATHON or rng.random() < content.FSP_TEAM_SHARE[discipline]
        results.append(
            {
                "id": _registry_id("ach", key, index),
                "event_name": event_name,
                "event_kind": kind.value,
                "discipline": item["discipline"],
                "level": item["level"],
                "year": item["year"],
                "place": item["place"],
                "result": FspOutcome.from_place(item["place"]).value,
                "participation": (
                    FspParticipation.TEAM if team else FspParticipation.INDIVIDUAL
                ).value,
                "team_name": rng.choice(content.FSP_TEAM_NAMES) if team else None,
            }
        )
    return results, _titles(rng, key, results)


def _titles(rng: random.Random, key: str, results: Sequence[Record]) -> list[Record]:
    """At most one sport rank or title, earned by the best individual-or-team result."""
    if not results:
        return []
    best = min(results, key=lambda item: (item["place"] or 99, item["level"] != "national"))
    place = best["place"]
    national = best["level"] == FspEventLevel.NATIONAL.value
    kind: FspTitleKind | None
    if place is not None and place <= 3 and national:  # noqa: PLR2004
        kind = FspTitleKind.KMS if rng.random() < 0.5 else FspTitleKind.RANK_1  # noqa: PLR2004
    elif place is not None and place <= 3:  # noqa: PLR2004
        kind = FspTitleKind.RANK_1 if rng.random() < 0.6 else None  # noqa: PLR2004
    elif place is not None:
        kind = FspTitleKind.RANK_2 if rng.random() < 0.4 else None  # noqa: PLR2004
    else:
        kind = FspTitleKind.RANK_3 if rng.random() < 0.3 else None  # noqa: PLR2004
    if kind is None:
        return []
    return [
        {
            "id": _registry_id("ttl", key, 0),
            "kind": kind.value,
            "discipline": best["discipline"],
            "awarded_year": best["year"],
        }
    ]


def _fsp_sentence(achievements: Sequence[Record]) -> str | None:
    if not achievements:
        return None
    placed = [item for item in achievements if item["place"] is not None]
    if not placed:
        discipline = FspDiscipline(achievements[0]["discipline"])
        return f"Участвую в соревнованиях ФСП по {content.FSP_DISCIPLINE_DATIVE[discipline]}."
    best = min(placed, key=lambda item: (item["place"], item["level"] != "national", -item["year"]))
    label = content.FSP_DISCIPLINE_LABELS[FspDiscipline(best["discipline"])]
    details = f"{best['event_name']} ({label}, {best['year']})"
    if best["place"] <= 3:  # noqa: PLR2004
        return f"{best['place']}-е место — {details}."
    return f"Финал — {details}, {best['place']}-е место."


def _about(
    rng: random.Random,
    person: _Person,
    *,
    track: Track,
    grade: Grade,
    years: int,
    university: content.University | None,
    work_formats: Sequence[WorkFormat],
    relocation_ready: bool,
    achievements: Sequence[Record],
) -> str:
    domain = rng.choice(track.domains or content.DOMAINS)
    focus = rng.sample(list(track.work), 2)
    parts: list[str] = []

    if grade == Grade.INTERN and university is not None:
        major = rng.choice(university.majors)
        if rng.random() < 0.7:  # noqa: PLR2004
            student = person.pick("Студент", "Студентка")
            course = rng.randint(3, 5)
            parts.append(f"{student} {course}-го курса {university.name}, направление «{major}».")
        else:
            graduate = person.pick("Выпускник", "Выпускница")
            parts.append(
                f"{graduate} {university.name} {CURRENT_YEAR} года, направление «{major}»."
            )
        parts.append(f"В учебных и пет-проектах — {focus[0]}.")
        parts.append(
            "Ищу стажировку, где смогу решать реальные задачи рядом с опытными инженерами."
        )
    elif grade == Grade.JUNIOR:
        experience = ("Полгода", "Год", "Два года")[years]
        parts.append(f"{experience} коммерческого опыта {domain}.")
        parts.append(f"В фокусе: {focus[0]}, {focus[1]}.")
        parts.append("Хочу расти в команде с культурой код-ревью и наставничества.")
    elif grade == Grade.LEAD:
        lead_years = rng.randint(2, max(2, years - 4))
        team = rng.randint(5, 14)
        parts.append(
            f"{years} {years_word(years)} в IT, последние {lead_years} — руковожу командой "
            f"из {team} человек."
        )
        parts.append(f"В зоне ответственности: {focus[0]}, {focus[1]}.")
        parts.append(rng.choice(content.LEAD_LINES))
    else:
        recent = rng.randint(1, years - 1)
        parts.append(f"{years} {years_word(years)} в IT, из них {recent} — {domain}.")
        parts.append(f"В фокусе: {focus[0]}, {focus[1]}.")
        if grade == Grade.SENIOR:
            parts.append(rng.choice(content.SENIOR_LINES))

    fsp = _fsp_sentence(achievements)
    if fsp:
        parts.append(fsp)

    if relocation_ready:
        parts.append(f"{person.pick('Готов', 'Готова')} к релокации.")
    elif WorkFormat.REMOTE in work_formats and rng.random() < 0.5:  # noqa: PLR2004
        parts.append(f"{person.pick('Открыт', 'Открыта')} к удалённой работе.")
    elif rng.random() < 0.4:  # noqa: PLR2004
        parts.append(rng.choice(content.CLOSING_LINES))
    return " ".join(parts)


def _soft_skills(rng: random.Random, grade: Grade) -> list[str]:
    skills = rng.sample(list(content.SOFT_SKILLS), rng.randint(2, 3))
    if grade in (Grade.SENIOR, Grade.LEAD):
        skills.append(rng.choice(content.LEADERSHIP_SKILLS))
    return skills


def _home(rng: random.Random, grade: Grade) -> tuple[content.City, content.University | None]:
    # Interns live where they study; juniors mostly too.
    if grade == Grade.INTERN or (grade == Grade.JUNIOR and rng.random() < 0.6):  # noqa: PLR2004
        # Each city keeps its share however many universities it has.
        per_city = Counter(university.city for university in content.UNIVERSITIES)
        weights = [
            content.CITIES_BY_NAME[university.city].weight / per_city[university.city]
            for university in content.UNIVERSITIES
        ]
        university = rng.choices(content.UNIVERSITIES, weights=weights)[0]
        return content.CITIES_BY_NAME[university.city], university
    weights = [city.weight for city in content.CITIES]
    return rng.choices(content.CITIES, weights=weights)[0], None


def _candidate(
    rng: random.Random,
    index: int,
    track: Track,
    grade: Grade,
    registry: _Registry,
    *,
    hidden: bool,
    untested: bool,
) -> Record:
    demo = index == 0
    person = _person(rng, track, registry)
    email = DEMO_CANDIDATE_EMAIL if demo else _email(person, registry)
    city, university = _home(rng, grade)
    if demo:
        city = content.CITIES_BY_NAME["Москва"]

    low, high = EXPERIENCE_YEARS[grade]
    years = rng.randint(low, high)
    patterns = (
        content.INTERN_WORK_FORMAT_PATTERNS
        if grade == Grade.INTERN
        else content.WORK_FORMAT_PATTERNS
    )
    # The demo account sees both remote and Moscow office vacancies in its feed.
    work_formats = (
        [WorkFormat.REMOTE, WorkFormat.HYBRID] if demo else list(_weighted(rng, patterns))
    )
    # Relocation only makes sense for someone who would work from an office.
    relocation_ready = work_formats != [WorkFormat.REMOTE] and rng.random() < 0.25  # noqa: PLR2004

    key = f"cand-{index + 1:03d}"
    fsp_share = content.FSP_LINK_SHARE[grade] + track.fsp_bonus
    linked = demo or rng.random() < fsp_share
    achievements: list[Record] = []
    titles: list[Record] = []
    if linked:
        registry.fsp_linked += 1
        if demo or registry.fsp_linked % FSP_LINKED_WITHOUT_RESULTS_EVERY:
            achievements = _achievements(rng, track, grade, years, city)
            achievements, titles = _registry_fields(key, achievements)

    assessed_days_ago = None if untested else rng.randint(2, 240)
    score = None if untested else round(rng.triangular(60, 99, 80), 1)
    extra_low, extra_high = RESUME_EXTRA_STACK[grade]

    return {
        "key": key,
        "track": track.key,
        "email": email,
        "display_name": f"{person.first} {person.last}",
        "headline": _headline(rng, track, grade),
        "about": _about(
            rng,
            person,
            track=track,
            grade=grade,
            years=years,
            university=university,
            work_formats=work_formats,
            relocation_ready=relocation_ready,
            achievements=achievements,
        ),
        "specialization": track.specialization,
        "grade": grade.value,
        "experience_years": years,
        "stack": _stack(rng, track.core, track.extra, rng.randint(extra_low, extra_high)),
        "soft_skills": _soft_skills(rng, grade),
        "english_level": _weighted(rng, content.ENGLISH_LEVELS[grade]),
        "city": city.name,
        "relocation_ready": relocation_ready,
        "work_formats": [work_format.value for work_format in work_formats],
        "salary_expectation": _salary_expectation(rng, track, grade, years, city),
        "assessment_score": score,
        "assessed_days_ago": assessed_days_ago,
        "registered_days_ago": (assessed_days_ago or 0) + rng.randint(1, 60),
        "fsp_member_id": _fsp_member_id(rng, registry) if linked else None,
        "fsp_achievements": achievements,
        "fsp_titles": titles,
        "phone": _phone(rng) if demo or rng.random() < 0.85 else None,  # noqa: PLR2004
        "telegram": (
            _telegram(rng, person, registry) if demo or rng.random() < 0.75 else None  # noqa: PLR2004
        ),
        "is_visible_to_employers": not hidden,
    }


def build_candidates(rng: random.Random) -> list[Record]:
    plan = _candidate_plan(rng)
    others = range(1, len(plan))
    hidden = set(rng.sample(others, HIDDEN_CANDIDATES))
    untested = set(rng.sample(others, UNTESTED_CANDIDATES))
    registry = _Registry(emails={DEMO_CANDIDATE_EMAIL})
    return [
        _candidate(
            rng,
            index,
            track,
            grade,
            registry,
            hidden=index in hidden,
            untested=index in untested,
        )
        for index, (track, grade) in enumerate(plan)
    ]


def _vacancy_salary(
    rng: random.Random, track: Track, plan: VacancyPlan, city: content.City
) -> tuple[int, int]:
    location = content.REMOTE_SALARY_FACTOR if plan.work_format == WorkFormat.REMOTE else 1.0
    center = (
        content.GRADE_SALARY[plan.grade]
        * content.SPECIALIZATION_SALARY_FACTOR[track.specialization]
        * city.salary_factor
        * location
        * rng.uniform(0.92, 1.12)
    )
    salary_from = round_salary(center * rng.uniform(0.82, 0.9))
    salary_to = round_salary(center * rng.uniform(1.1, 1.25))
    return salary_from, max(salary_to, salary_from + 10_000)


def _vacancy_description(
    rng: random.Random, track: Track, plan: VacancyPlan, stack: Sequence[str], city: content.City
) -> str:
    tasks = rng.sample(list(track.work), 3)
    # The core is covered by the track requirements; list the rest of the stack. Only tool names:
    # Russian terms ("Тест-дизайн") would need declension.
    tools = [item for item in stack if item[0].isascii()]
    named = [item for item in tools if item not in track.core][:3] or tools[:3]
    requirements = [
        content.EXPERIENCE_REQUIREMENTS[plan.grade],
        f"{content.STACK_REQUIREMENT_PREFIX[plan.grade]} {_join(named)}",
        *rng.sample(list(track.requirements), 2),
    ]
    pluses = rng.sample(list(track.pluses), 2)
    if rng.random() < 0.4:  # noqa: PLR2004
        pluses.append(content.FSP_PLUS)
    conditions = [content.FORMAT_CONDITIONS[plan.work_format].format(city=city.locative)]
    if plan.grade in content.GRADE_CONDITIONS:
        conditions.append(content.GRADE_CONDITIONS[plan.grade])
    conditions.extend(rng.sample(list(content.CONDITIONS), 2))

    sections = (
        plan.team,
        f"Задачи:\n{_bullets(tasks)}",
        f"Требования:\n{_bullets(requirements)}",
        f"Будет плюсом:\n{_bullets(pluses)}",
        f"Условия:\n{_bullets(conditions)}",
    )
    return "\n\n".join(sections)


def _vacancy(rng: random.Random, company: CompanyPlan, index: int, plan: VacancyPlan) -> Record:
    track = content.TRACKS_BY_KEY[plan.track]
    city = content.CITIES_BY_NAME[company.city]
    pinned = [item for item in plan.stack if item not in track.core]
    pool = [item for item in track.extra if item not in pinned]
    extra_size = max(0, VACANCY_EXTRA_STACK[plan.grade] - len(pinned))
    stack = [*track.core, *pinned, *rng.sample(pool, min(extra_size, len(pool)))]
    salary_from, salary_to = _vacancy_salary(rng, track, plan, city)
    return {
        "key": f"{company.key}-{index:02d}",
        "track": track.key,
        "company_key": company.key,
        "title": plan.title,
        "specialization": track.specialization,
        "grade": plan.grade.value,
        "stack": stack,
        "salary_from": salary_from,
        "salary_to": salary_to,
        "work_format": plan.work_format.value,
        "city": None if plan.work_format == WorkFormat.REMOTE else company.city,
        "description": _vacancy_description(rng, track, plan, stack, city),
        "published_days_ago": plan.published_days_ago,
    }


def build_companies(rng: random.Random) -> tuple[list[Record], list[Record]]:
    companies: list[Record] = []
    vacancies: list[Record] = []
    for position, company in enumerate(content.COMPANIES):
        if position < len(DEMO_EMPLOYER_EMAILS):
            owner = DEMO_EMPLOYER_EMAILS[position]
        else:
            owner = f"recruiter@{company.key}.{EMAIL_DOMAIN}"
        companies.append(
            {
                "key": company.key,
                "owner_email": owner,
                "name": company.name,
                "industry": company.industry,
                "city": company.city,
                "size": company.size,
                "description": company.description,
                "website": f"https://{company.key}.{EMAIL_DOMAIN}",
                "contact_email": f"hr@{company.key}.{EMAIL_DOMAIN}",
                "registered_days_ago": rng.randint(200, 900),
            }
        )
        vacancies.extend(
            _vacancy(rng, company, index, plan)
            for index, plan in enumerate(company.vacancies, start=1)
        )
    return companies, vacancies


def _registry_of(companies: Sequence[Record], candidates: Sequence[Record]) -> _Registry:
    registry = _Registry()
    for company in companies:
        registry.emails.add(str(company["owner_email"]))
        registry.emails.add(str(company["contact_email"]))
    for candidate in candidates:
        registry.names.add(str(candidate["display_name"]))
        registry.emails.add(str(candidate["email"]))
        if candidate["telegram"]:
            registry.handles.add(str(candidate["telegram"]))
        if candidate["fsp_member_id"]:
            registry.fsp_ids.add(str(candidate["fsp_member_id"]))
    return registry


def _as_vacancy(vacancy: VacancyFixture) -> Vacancy:
    """The same row the loader inserts, without a database."""
    return Vacancy(
        company_id=uuid.UUID(int=0),
        title=vacancy.title,
        description=vacancy.description,
        specialization=vacancy.specialization,
        grade=vacancy.grade,
        stack=list(vacancy.stack),
        salary_from=vacancy.salary_from,
        salary_to=vacancy.salary_to,
        work_format=vacancy.work_format,
        city=vacancy.city,
        **vacancy_details(vacancy),
    )


def _search_query(vacancy: VacancyFixture):
    """Filters a recruiter gets by selecting this vacancy."""
    return candidate_query(
        vacancy_filters(_as_vacancy(vacancy)),
        text=None,
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _search_facts(candidate: CandidateFixture) -> FilterFacts:
    details = candidate_details(candidate, datetime(2026, 1, 1, tzinfo=UTC))
    status = details["job_status"]
    employment = details["employment_types"]
    if not isinstance(status, JobStatus) or not isinstance(employment, list):
        msg = f"{candidate.key}: candidate details are incomplete"
        raise TypeError(msg)
    return FilterFacts(
        specialization=candidate.specialization,
        grade=candidate.grade,
        verified=candidate.assessment_score is not None,
        fsp_marks=fsp_marks(candidate.fsp_achievements),
        experience=candidate.experience_years,
        stack=frozenset(normalize_term(item) for item in candidate.stack),
        salary=candidate.salary_expectation,
        formats=frozenset(item.value for item in candidate.work_formats),
        city=normalize_term(candidate.city) if candidate.city else None,
        relocation=candidate.relocation_ready,
        employment=frozenset(str(item) for item in employment),
        status=status.value,
        last_active=None,
    )


def match_counts(
    candidates: Sequence[CandidateFixture], vacancies: Sequence[VacancyFixture]
) -> list[int]:
    """How many visible candidates pass each vacancy's preset filters."""
    visible = [_search_facts(item) for item in candidates if item.is_visible_to_employers]
    return [
        sum(passes(facts, _search_query(vacancy)) for facts in visible) for vacancy in vacancies
    ]


def _expectation(vacancy: VacancyFixture) -> int:
    """A grade-typical salary that still fits this vacancy's ceiling."""
    factor = content.SPECIALIZATION_SALARY_FACTOR[vacancy.specialization]
    typical = round_salary(content.GRADE_SALARY[vacancy.grade] * factor)
    return min(typical, vacancy.salary_to)


def _cover_stack(vacancy: VacancyFixture, cohort: Sequence[VacancyFixture]) -> list[str]:
    stack: list[str] = []
    for item in (vacancy, *cohort):
        for technology in item.stack:
            if technology not in stack:
                stack.append(technology)
    return stack


def _cover_disciplines(cohort: Sequence[VacancyFixture]) -> list[FspDiscipline]:
    found: list[FspDiscipline] = []
    for item in cohort:
        discipline = vacancy_details(item)["fsp_discipline"]
        if isinstance(discipline, FspDiscipline) and discipline not in found:
            found.append(discipline)
    return found


def _university(city_name: str) -> content.University:
    for university in content.UNIVERSITIES:
        if university.city == city_name:
            return university
    return content.UNIVERSITIES[0]


def _matching_candidate(
    rng: random.Random,
    index: int,
    vacancy: VacancyFixture,
    vacancies: Sequence[VacancyFixture],
    registry: _Registry,
) -> Record:
    """A visible, verified profile that passes this vacancy and the similar ones it can."""
    track = content.TRACKS_BY_KEY[vacancy.track]
    grade = vacancy.grade
    expectation = _expectation(vacancy)
    cohort = [
        item
        for item in vacancies
        if item.specialization == vacancy.specialization
        and item.grade == grade
        and item.salary_to >= expectation
    ]
    person = _person(rng, track, registry)
    city = content.CITIES_BY_NAME["Москва"]
    years = EXPERIENCE_YEARS[grade][0]
    work_formats = [WorkFormat.REMOTE, WorkFormat.HYBRID, WorkFormat.OFFICE]
    disciplines = _cover_disciplines(cohort)
    key = f"cand-{index + 1:04d}"
    achievements: list[Record] = []
    titles: list[Record] = []
    if disciplines:
        raw = [
            {
                "event_name": content.FSP_NATIONAL_EVENTS[0],
                "discipline": discipline.value,
                "level": FspEventLevel.NATIONAL.value,
                "year": CURRENT_YEAR - 1,
                "place": 1,
            }
            for discipline in disciplines
        ]
        achievements, titles = _registry_fields(key, raw)

    return {
        "key": key,
        "track": track.key,
        "email": _email(person, registry),
        "display_name": f"{person.first} {person.last}",
        "headline": _headline(rng, track, grade),
        "about": _about(
            rng,
            person,
            track=track,
            grade=grade,
            years=years,
            university=_university(city.name) if grade == Grade.INTERN else None,
            work_formats=work_formats,
            relocation_ready=True,
            achievements=achievements,
        ),
        "specialization": track.specialization,
        "grade": grade.value,
        "experience_years": years,
        "stack": _cover_stack(vacancy, cohort),
        "soft_skills": _soft_skills(rng, grade),
        "english_level": _weighted(rng, content.ENGLISH_LEVELS[grade]),
        "city": city.name,
        "relocation_ready": True,
        "work_formats": [item.value for item in work_formats],
        "salary_expectation": expectation,
        "assessment_score": 84.0,
        "assessed_days_ago": 30,
        "registered_days_ago": 45,
        "fsp_member_id": _fsp_member_id(rng, registry) if disciplines else None,
        "fsp_achievements": achievements,
        "fsp_titles": titles,
        "phone": _phone(rng),
        "telegram": _telegram(rng, person, registry),
        "is_visible_to_employers": True,
    }


def _cover_vacancies(
    rng: random.Random,
    companies: Sequence[Record],
    candidates: list[Record],
    vacancies: Sequence[Record],
) -> list[Record]:
    """Adds candidates until every vacancy's own filters keep at least ten people."""
    registry = _registry_of(companies, candidates)
    vacancy_fixtures = [VacancyFixture.model_validate(item) for item in vacancies]
    queries = [_search_query(item) for item in vacancy_fixtures]
    facts = [
        _search_facts(CandidateFixture.model_validate(item))
        for item in candidates
        if item["is_visible_to_employers"]
    ]
    counts = [sum(passes(item, query) for item in facts) for query in queries]
    order = sorted(
        range(len(vacancy_fixtures)),
        key=lambda index: (vacancy_fixtures[index].salary_to, vacancy_fixtures[index].key),
    )
    index = len(candidates)
    for vacancy_index in order:
        added = 0
        while counts[vacancy_index] < MATCHES_PER_VACANCY:
            record = _matching_candidate(
                rng, index, vacancy_fixtures[vacancy_index], vacancy_fixtures, registry
            )
            index += 1
            added += 1
            fixture = CandidateFixture.model_validate(record)
            fact = _search_facts(fixture)
            if not passes(fact, queries[vacancy_index]):
                missed = ", ".join(failed_groups(fact, queries[vacancy_index]))
                key = vacancy_fixtures[vacancy_index].key
                msg = f"{record['key']} does not match {key}: {missed}"
                raise RuntimeError(msg)
            candidates.append(record)
            facts.append(fact)
            for other, query in enumerate(queries):
                if passes(fact, query):
                    counts[other] += 1
            if added > MATCHES_PER_VACANCY:
                msg = f"{vacancy_fixtures[vacancy_index].key} still has {counts[vacancy_index]}"
                raise RuntimeError(msg)
    return candidates


def build_dataset(seed: int = SEED) -> dict[str, list[Record]]:
    rng = random.Random(seed)  # noqa: S311 - reproducible fake data, not a security context
    companies, vacancies = build_companies(rng)
    candidates = build_candidates(rng)
    candidates = _cover_vacancies(rng, companies, candidates, vacancies)
    return {"companies": companies, "vacancies": vacancies, "candidates": candidates}


def dump(records: list[Record]) -> str:
    return json.dumps(records, ensure_ascii=False, indent=2) + "\n"


def write_dataset(dataset: dict[str, list[Record]], data_dir: Path = DATA_DIR) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    for name, records in dataset.items():
        (data_dir / f"{name}.json").write_text(dump(records), encoding="utf-8", newline="\n")


def main() -> None:
    dataset = build_dataset()
    write_dataset(dataset)
    summary = ", ".join(f"{name}: {len(records)}" for name, records in dataset.items())
    print(f"Demo dataset written to {DATA_DIR} ({summary})")


if __name__ == "__main__":
    main()
