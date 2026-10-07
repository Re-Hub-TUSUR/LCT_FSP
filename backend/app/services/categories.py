"""MVP dictionary of specializations and grades (ТЗ: the team compiles it from common IT terms)."""

from app.models.enums import FspDiscipline, Grade, WorkFormat
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

FSP_DISCIPLINE_LABELS: dict[FspDiscipline, str] = {
    FspDiscipline.ALGORITHMIC: "алгоритмическое программирование",
    FspDiscipline.PRODUCT: "продуктовое программирование",
    FspDiscipline.SECURITY: "программирование систем ИБ",
    FspDiscipline.ROBOTICS: "программирование робототехники",
    FspDiscipline.UAV: "программирование БАС",
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
