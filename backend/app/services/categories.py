"""MVP dictionary of specializations and grades (ТЗ: the team compiles it from common IT terms)."""

from app.models.enums import (
    EmploymentType,
    FspDiscipline,
    FspEventKind,
    FspOutcome,
    FspTitleKind,
    Grade,
    VacancyBenefit,
    WorkFormat,
)
from app.schemas.category import Category, CategoryDictionary, GradeRead, SpecializationRead
from app.search.synonyms import SYNONYM_GROUPS

SPECIALIZATIONS: dict[str, str] = {
    "backend": "Backend-разработка",
    "frontend": "Frontend-разработка",
    "fullstack": "Fullstack-разработка",
    "mobile": "Мобильная разработка",
    "data-science": "Data Science / ML",
    "data-engineering": "Data Engineering",
    "devops": "DevOps / SRE",
    "qa": "Тестирование (QA)",
    "security": "Информационная безопасность",
    "gamedev": "Разработка игр",
}

GRADE_LABELS: dict[Grade, str] = {
    Grade.INTERN: "Стажёр",
    Grade.JUNIOR: "Junior",
    Grade.MIDDLE: "Middle",
    Grade.SENIOR: "Senior",
    Grade.LEAD: "Lead",
}

WORK_FORMAT_LABELS: dict[WorkFormat, str] = {
    WorkFormat.OFFICE: "Офис",
    WorkFormat.HYBRID: "Гибрид",
    WorkFormat.REMOTE: "Удалённо",
}

EMPLOYMENT_LABELS: dict[EmploymentType, str] = {
    EmploymentType.FULL: "полная занятость",
    EmploymentType.PART: "частичная занятость",
    EmploymentType.PROJECT: "проектная работа",
    EmploymentType.INTERNSHIP: "стажировка",
}

BENEFIT_LABELS: dict[VacancyBenefit, str] = {
    VacancyBenefit.DMS: "ДМС",
    VacancyBenefit.FLEXIBLE_START: "гибкое начало дня",
    VacancyBenefit.LABOR_CODE: "оформление по ТК РФ",
}

FSP_DISCIPLINE_LABELS: dict[FspDiscipline, str] = {
    FspDiscipline.ALGORITHMIC: "алгоритмическое программирование",
    FspDiscipline.PRODUCT: "продуктовое программирование",
    FspDiscipline.SECURITY: "программирование систем ИБ",
    FspDiscipline.ROBOTICS: "программирование робототехники",
    FspDiscipline.UAV: "программирование БАС",
}

FSP_OUTCOME_LABELS: dict[FspOutcome, str] = {
    FspOutcome.WINNER: "победитель",
    FspOutcome.PRIZEWINNER: "призёр",
    FspOutcome.FINALIST: "финалист",
    FspOutcome.PARTICIPANT: "участник",
}

FSP_EVENT_KIND_LABELS: dict[FspEventKind, str] = {
    FspEventKind.CHAMPIONSHIP: "чемпионат",
    FspEventKind.CUP: "кубок",
    FspEventKind.HACKATHON: "хакатон",
    FspEventKind.OLYMPIAD: "олимпиада",
}

FSP_TITLE_LABELS: dict[FspTitleKind, str] = {
    FspTitleKind.RANK_3: "3-й разряд",
    FspTitleKind.RANK_2: "2-й разряд",
    FspTitleKind.RANK_1: "1-й разряд",
    FspTitleKind.KMS: "КМС",
    FspTitleKind.MS: "МС",
    FspTitleKind.MSMK: "МСМК",
    FspTitleKind.ZMS: "ЗМС",
}


def category_for(specialization: str | None, grade: Grade | None) -> Category | None:
    """Category = specialization + grade; None until both are known."""
    if specialization is None or grade is None:
        return None
    label = f"{SPECIALIZATIONS.get(specialization, specialization)} · {GRADE_LABELS[grade]}"
    return Category(
        code=f"{specialization}:{grade.value}",
        label=label,
        specialization=specialization,
        grade=grade,
    )


def get_dictionary() -> CategoryDictionary:
    return CategoryDictionary(
        specializations=[
            SpecializationRead(code=code, label=label) for code, label in SPECIALIZATIONS.items()
        ],
        grades=[GradeRead(code=grade, label=label) for grade, label in GRADE_LABELS.items()],
        synonyms=[list(group) for group in SYNONYM_GROUPS],
    )
