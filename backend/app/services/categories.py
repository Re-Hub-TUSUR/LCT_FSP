"""MVP dictionary of specializations and grades (ТЗ: the team compiles it from common IT terms)."""

from app.models.enums import Grade
from app.schemas.category import CategoryDictionary, GradeRead, SpecializationRead

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


def get_dictionary() -> CategoryDictionary:
    return CategoryDictionary(
        specializations=[
            SpecializationRead(code=code, label=label) for code, label in SPECIALIZATIONS.items()
        ],
        grades=[GradeRead(code=grade, label=label) for grade, label in GRADE_LABELS.items()],
    )
