"""Built-in values of the admin dictionaries and parameters."""

from dataclasses import dataclass
from typing import Final

from app.models.enums import Grade


@dataclass(frozen=True, slots=True)
class AdminGrade:
    code: str
    label: str
    # The level of the platform's own 5-step scale this one belongs to.
    base: Grade


# The 11-level scale of the admin panel. Candidates and vacancies still use `Grade`;
# `base` tells which of its values a level falls into.
GRADES: Final[tuple[AdminGrade, ...]] = (
    AdminGrade("junior-minus", "Junior-", Grade.JUNIOR),
    AdminGrade("junior", "Junior", Grade.JUNIOR),
    AdminGrade("junior-plus", "Junior+", Grade.JUNIOR),
    AdminGrade("middle-minus", "Middle-", Grade.MIDDLE),
    AdminGrade("middle", "Middle", Grade.MIDDLE),
    AdminGrade("middle-plus", "Middle+", Grade.MIDDLE),
    AdminGrade("senior-minus", "Senior-", Grade.SENIOR),
    AdminGrade("senior", "Senior", Grade.SENIOR),
    AdminGrade("senior-plus", "Senior+", Grade.SENIOR),
    AdminGrade("lead", "Lead", Grade.LEAD),
    AdminGrade("head", "Head", Grade.LEAD),
)
GRADE_CODES: Final = frozenset(grade.code for grade in GRADES)


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    key: str
    label: str
    default: int
    minimum: int
    maximum: int
    unit: str


PARAMETERS: Final[tuple[ParameterSpec, ...]] = (
    ParameterSpec("grade_change_cooldown_days", "T_кулдаун смены грейда", 90, 0, 365, "дней"),
    ParameterSpec("target_solve_min", "Целевая доля решивших: от", 50, 0, 100, "%"),
    ParameterSpec("target_solve_max", "Целевая доля решивших: до", 70, 0, 100, "%"),
    ParameterSpec("variant_spread_pp", "Порог разброса вариантов", 10, 0, 100, "п.п."),
    ParameterSpec("leak_jump_pp", "Порог сигнала утечки (неделя к неделе)", 20, 0, 100, "п.п."),
    ParameterSpec("fake_vacancy_share", "Порог фиктивных вакансий", 30, 0, 100, "%"),
    ParameterSpec(
        "fake_vacancy_min_closed", "Фиктивные вакансии: минимум закрытий", 10, 1, 10_000, "шт."
    ),
    ParameterSpec(
        "min_attempts_for_flags", "Минимум попыток для флагов по заданию", 30, 1, 100_000, "шт."
    ),
    ParameterSpec(
        "invite_anomaly_factor",
        "Аномалия приглашений: во сколько раз выше медианы",
        3,
        2,
        100,
        "раз",
    ),
    ParameterSpec(
        "invite_anomaly_min", "Аномалия приглашений: минимум за сутки", 10, 1, 10_000, "шт."
    ),
    ParameterSpec("low_response_share", "Низкая доля ответов кандидатам", 20, 0, 100, "%"),
    ParameterSpec(
        "low_response_min_inbound", "Доля ответов: минимум откликов", 10, 1, 10_000, "шт."
    ),
)
PARAMETER_SPECS: Final = {spec.key: spec for spec in PARAMETERS}
DEFAULTS: Final = {spec.key: spec.default for spec in PARAMETERS}


@dataclass(frozen=True, slots=True)
class HardcodedValue:
    """A value the platform reads from code or settings, not from these parameters."""

    parameter: str
    where: str


# Shown in the parameters screen: changing these values here does not change the places below.
HARDCODED: Final[tuple[HardcodedValue, ...]] = (
    HardcodedValue(
        "T_кулдаун смены грейда",
        "backend/app/core/config.py: assessment_grade_change_days (90), "
        "assessment_tests.grade_change_days",
    ),
    HardcodedValue(
        "Повторная попытка после провала",
        "backend/app/core/config.py: assessment_retry_days (7)",
    ),
    HardcodedValue(
        "Проходной балл и минимум по вопросам",
        "шаблон теста: assessment_tests.pass_score, quiz_min (раздел «Тесты»); "
        "стартовые значения в backend/app/seed/data/assessment/tests.json",
    ),
    HardcodedValue(
        "Граница «рекомендуем следующий грейд»",
        "шаблон теста: assessment_tests.recommend_score; без него "
        "backend/app/core/config.py: assessment_recommend_score (85)",
    ),
    HardcodedValue(
        "Специализации и грейды",
        "backend/app/services/categories.py: SPECIALIZATIONS, GRADE_LABELS; "
        "app/models/enums.py: Grade (5 уровней)",
    ),
    HardcodedValue(
        "Демо-данные",
        "backend/app/seed/loader.py: GRADE_CHANGE_DAYS (90), RECOMMEND_SCORE (85)",
    ),
)
