"""Registration fields of the ТЗ for the demo rows, derived from the fixtures.

Every value comes from a stable hash of the fixture key, so re-seeding gives the same data.
"""

import zlib
from datetime import date, datetime, timedelta
from typing import Final

from app.models.enums import (
    EmploymentType,
    FspDiscipline,
    FspResult,
    FspSync,
    Grade,
    JobStatus,
    VacancyBenefit,
)
from app.seed.fixtures import CandidateFixture, CompanyFixture, VacancyFixture

# The first companies of the dataset have an approved Минцифры extract: the check mark is
# visible in the feed. The first one is the demo employer.
ACCREDITED_COMPANIES: Final = 2

_FIRST_NAMES: Final = ("Анна", "Дмитрий", "Екатерина", "Сергей", "Ольга", "Алексей", "Мария")
_LAST_NAMES: Final = ("Смирнова", "Волков", "Кузнецова", "Морозов", "Соколова", "Лебедев")
_EMPLOYERS: Final = (
    "Сбер",
    "Т-Банк",
    "Яндекс",
    "VK",
    "Контур",
    "Ozon",
    "Авито",
    "Лаборатория Касперского",
    "Positive Technologies",
    "Студия веб-разработки",
)
_UNIVERSITIES: Final = (
    ("ТУСУР", "Программная инженерия"),
    ("ИТМО", "Информатика и вычислительная техника"),
    ("МФТИ", "Прикладная математика и информатика"),
    ("НГУ", "Математическое обеспечение"),
    ("УрФУ", "Информационные системы и технологии"),
    ("ВШЭ", "Программная инженерия"),
)
_MIN_EXPERIENCE: Final = {
    Grade.INTERN: 0,
    Grade.JUNIOR: 0,
    Grade.MIDDLE: 1,
    Grade.SENIOR: 3,
    Grade.LEAD: 5,
}


def _pick(key: str, salt: str, size: int) -> int:
    return zlib.crc32(f"{salt}:{key}".encode()) % size


def inn(index: int) -> str:
    """A valid 10-digit organisation INN, unique per position in the dataset."""
    digits = [int(char) for char in f"77{index + 1:07d}"]
    weights = (2, 4, 10, 3, 5, 9, 4, 6, 8)
    check = sum(d * w for d, w in zip(digits, weights, strict=True)) % 11 % 10
    return "".join(map(str, digits)) + str(check)


def company_details(company: CompanyFixture, index: int) -> dict[str, object]:
    return {
        "inn": inn(index),
        "ogrn": f"10277{index + 1:08d}",
        "kpp": f"77{_pick(company.key, 'kpp', 100):02d}01001",
        "legal_address": f"г. {company.city}, ул. Технопарковая, д. {index + 1}",
    }


def person(key: str) -> tuple[str, str]:
    first = _FIRST_NAMES[_pick(key, "first", len(_FIRST_NAMES))]
    last = _LAST_NAMES[_pick(key, "last", len(_LAST_NAMES))]
    # Russian surnames agree with the first name: -а/-я names are female.
    female = first.endswith(("а", "я"))
    if not female and last.endswith("а"):
        last = last[:-1]
    if female and not last.endswith("а"):
        last = f"{last}а"
    return first, last


def last_active(key: str, now: datetime) -> datetime:
    """Most demo accounts were active this month, some long ago (the 30-day filter)."""
    return now - timedelta(days=_pick(key, "active", 60), hours=_pick(key, "hour", 24))


def _month(day: date) -> str:
    return f"{day:%Y-%m}"


def candidate_details(candidate: CandidateFixture, now: datetime) -> dict[str, object]:
    key = candidate.key
    today = now.date()
    if not candidate.is_visible_to_employers:
        status = JobStatus.NOT_LOOKING
    elif _pick(key, "status", 3) == 0:
        status = JobStatus.ACTIVE
    else:
        status = JobStatus.OPEN

    employment = [EmploymentType.FULL]
    if candidate.grade == Grade.INTERN:
        employment = [EmploymentType.INTERNSHIP, EmploymentType.PART]
    elif _pick(key, "project", 3) == 0:
        employment.append(EmploymentType.PROJECT)

    entries: list[dict[str, object]] = []
    years = candidate.experience_years
    if years:
        start = today.replace(day=1) - timedelta(days=365 * years)
        if years >= 3:  # noqa: PLR2004 - a long career is split into two jobs
            middle = start + timedelta(days=365 * (years // 2))
            entries.append(_job(key, 0, start, middle, candidate.stack))
            start = middle + timedelta(days=31)
        entries.append(_job(key, 1, start, None, candidate.stack))

    university, specialty = _UNIVERSITIES[_pick(key, "edu", len(_UNIVERSITIES))]
    age = 21 + years + _pick(key, "age", 5)
    slug = candidate.email.split("@", 1)[0].replace(".", "-")
    return {
        "job_status": status,
        "employment_types": [item.value for item in employment],
        "birth_date": date(
            today.year - age, 1 + _pick(key, "month", 12), 1 + _pick(key, "day", 28)
        ),
        "experience_entries": entries,
        "no_experience": years == 0,
        "education": [
            {"institution": university, "specialty": specialty, "year": today.year - years - 1}
        ],
        "github_url": f"https://github.com/{slug}" if _pick(key, "github", 2) else None,
        "profile_display_consent": True,
        "fsp_sync": FspSync.YES if candidate.fsp_member_id else FspSync.NEVER,
    }


def _job(
    key: str, order: int, start: date, end: date | None, stack: list[str]
) -> dict[str, object]:
    return {
        "company": _EMPLOYERS[_pick(key, f"job{order}", len(_EMPLOYERS))],
        "position": "Разработчик" if order == 0 else "Инженер-разработчик",
        "start": _month(start),
        "end": _month(end) if end else None,
        "stack": stack[:4],
    }


def vacancy_details(vacancy: VacancyFixture) -> dict[str, object]:
    key = vacancy.key
    grades = [vacancy.grade]
    following = vacancy.grade.following
    if following is not None and _pick(key, "grades", 3) == 0:
        grades.append(following)
    split = max(1, (len(vacancy.stack) * 2 + 2) // 3)

    employment = [EmploymentType.FULL]
    if vacancy.grade == Grade.INTERN:
        employment = [EmploymentType.INTERNSHIP]
    elif _pick(key, "part", 4) == 0:
        employment.append(EmploymentType.PART)

    benefits = [VacancyBenefit.LABOR_CODE]
    if _pick(key, "dms", 2):
        benefits.append(VacancyBenefit.DMS)
    if _pick(key, "flex", 3) == 0:
        benefits.append(VacancyBenefit.FLEXIBLE_START)

    wants_fsp = _pick(key, "fsp", 4) == 0
    disciplines = list(FspDiscipline)
    return {
        "grades": [grade.value for grade in grades],
        "stack_required": vacancy.stack[:split],
        "stack_nice": vacancy.stack[split:],
        "relocation_help": vacancy.city is not None and _pick(key, "relocation", 4) == 0,
        "employment_types": [item.value for item in employment],
        "benefits": [item.value for item in benefits],
        "verified_grade_only": _pick(key, "verified", 5) != 0,
        "fsp_best_result": (
            (FspResult.FINALIST if _pick(key, "result", 2) else FspResult.PARTICIPANT)
            if wants_fsp
            else None
        ),
        "fsp_discipline": (disciplines[_pick(key, "discipline", 2)] if wants_fsp else None),
        "min_experience_years": _MIN_EXPERIENCE[vacancy.grade],
    }
