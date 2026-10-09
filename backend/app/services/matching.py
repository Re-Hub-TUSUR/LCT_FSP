"""Explainable matching of candidates and vacancies.

One scoring model serves both feeds:

- a candidate's feed ranks vacancies by `fit(candidate, vacancy)` with a freshness bonus;
- a recruiter's search ranks candidates by profile strength, or by `fit` with a profile-strength
  bonus when the recruiter hires for a specific vacancy.

The Elasticsearch query (`app/search/query.py`) reproduces these weights, so both search engines
order candidates the same way and the reasons shown on a card explain its actual position.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, Self

from app.models import CandidateProfile, FspDiscipline, FspEventLevel, Grade, Vacancy, WorkFormat
from app.models.enums import FspOutcome, FspParticipation, FspTitleKind
from app.services.categories import (
    FSP_DISCIPLINE_LABELS,
    FSP_EVENT_KIND_LABELS,
    FSP_OUTCOME_LABELS,
    FSP_TITLE_LABELS,
    GRADE_LABELS,
    SPECIALIZATIONS,
    WORK_FORMAT_LABELS,
    category_for,
)

GRADES: tuple[Grade, ...] = tuple(Grade)


@dataclass(frozen=True, slots=True)
class Weights:
    """Points out of 100 for each signal of the fit."""

    specialization: float = 20.0
    grade: float = 20.0
    stack: float = 25.0
    work_format: float = 10.0
    location: float = 5.0
    salary: float = 10.0
    # Side-specific: profile strength for recruiters, freshness of the vacancy for candidates.
    bonus: float = 10.0


WEIGHTS = Weights()
# Partial credit: related specialization, neighbouring grade, salary slightly above the range.
HALF = 0.5
# A candidate ready to move gets most, not all, of the location points.
RELOCATION_SHARE = 0.6
# A second resume in the vacancy's profession: below the priority one, above a related one.
SECOND_RESUME_SHARE = 0.75
# Expectation up to 10% above the top of the range still gets half of the salary points.
SALARY_TOLERANCE = 1.1

_RELATED: dict[str, frozenset[str]] = {
    "backend": frozenset({"fullstack", "data-engineering"}),
    "frontend": frozenset({"fullstack"}),
    "fullstack": frozenset({"backend", "frontend"}),
    "data-science": frozenset({"data-engineering"}),
    "data-engineering": frozenset({"data-science", "backend"}),
    "devops": frozenset({"security"}),
    "security": frozenset({"devops"}),
}


def related_specializations(specialization: str) -> frozenset[str]:
    """Specializations whose people often move into `specialization` (symmetric)."""
    direct = _RELATED.get(specialization, frozenset())
    reverse = {other for other, related in _RELATED.items() if specialization in related}
    return direct | reverse


def neighbour_grades(grade: Grade) -> tuple[Grade, ...]:
    index = GRADES.index(grade)
    return tuple(GRADES[i] for i in (index - 1, index + 1) if 0 <= i < len(GRADES))


# --- profile strength ---------------------------------------------------------------------------

# Points for the best FSP result: winner, prizewinner 2nd and 3rd place, finalist, participant.
FSP_POINTS: dict[FspEventLevel, tuple[float, float, float, float, float]] = {
    FspEventLevel.INTERNATIONAL: (0.40, 0.37, 0.34, 0.27, 0.17),
    FspEventLevel.NATIONAL: (0.38, 0.35, 0.32, 0.25, 0.15),
    FspEventLevel.REGIONAL: (0.30, 0.26, 0.23, 0.15, 0.08),
}
FSP_EXTRA_PER_RESULT = 0.02
# A team result is shared with teammates, so it weighs a little less than an individual one.
FSP_TEAM_SHARE = 0.9
# The highest sport rank or title adds to the FSP part, still within the cap.
FSP_TITLE_BONUS: dict[FspTitleKind, float] = {
    FspTitleKind.RANK_3: 0.01,
    FspTitleKind.RANK_2: 0.015,
    FspTitleKind.RANK_1: 0.02,
    FspTitleKind.KMS: 0.03,
    FspTitleKind.MS: 0.04,
    FspTitleKind.MSMK: 0.05,
    FspTitleKind.ZMS: 0.05,
}
FSP_CAP = 0.4
TEST_SHARE = 0.6
PRIZE_PLACES = 3


@dataclass(frozen=True, slots=True)
class FspScoredResult:
    """An FSP result as the ranking sees it."""

    event_name: str
    discipline: FspDiscipline
    level: FspEventLevel
    year: int
    place: int | None
    result: FspOutcome
    participation: FspParticipation = FspParticipation.INDIVIDUAL
    team_name: str | None = None

    @classmethod
    def placed(
        cls,
        event_name: str,
        discipline: FspDiscipline,
        level: FspEventLevel,
        year: int,
        place: int | None,
        **extra: Any,
    ) -> Self:
        """The registry's result for a place, e.g. 2 → prizewinner."""
        return cls(
            event_name, discipline, level, year, place, FspOutcome.from_place(place), **extra
        )


def _result_points(result: FspScoredResult) -> float:
    points = FSP_POINTS[result.level]
    if result.result == FspOutcome.WINNER:
        value = points[0]
    elif result.result == FspOutcome.PRIZEWINNER:
        # The place only orders prizewinners; without one the result counts as 2nd.
        place = result.place if result.place in (2, 3) else 2
        value = points[place - 1]
    elif result.result == FspOutcome.FINALIST:
        value = points[3]
    else:
        value = points[4]
    if result.participation == FspParticipation.TEAM:
        value *= FSP_TEAM_SHARE
    return value


def best_fsp_result(results: Sequence[FspScoredResult]) -> FspScoredResult | None:
    return max(results, key=lambda result: (_result_points(result), result.year), default=None)


def best_fsp_title(titles: Sequence[FspTitleKind]) -> FspTitleKind | None:
    order = list(FspTitleKind)
    return max(titles, key=order.index, default=None)


def fsp_points(results: Sequence[FspScoredResult], titles: Sequence[FspTitleKind] = ()) -> float:
    """0–0.4: the best result, a little for each further one, and the highest title."""
    best = best_fsp_result(results)
    title = best_fsp_title(titles)
    points = FSP_TITLE_BONUS[title] if title is not None else 0.0
    if best is not None:
        points += _result_points(best) + FSP_EXTRA_PER_RESULT * (len(results) - 1)
    return min(FSP_CAP, points)


def fsp_search_text(profile: CandidateProfile) -> str:
    """Words of the FSP history a recruiter may search by: «хакатон», «призёр», «КМС»…"""
    parts: list[str] = []
    for item in profile.fsp_achievements:
        parts += [
            item.event_name,
            FSP_EVENT_KIND_LABELS[item.event_kind],
            FSP_DISCIPLINE_LABELS[item.discipline],
            FSP_OUTCOME_LABELS[item.result],
        ]
        if item.team_name:
            parts += ["команда", item.team_name]
    for title in profile.fsp_titles:
        parts += [FSP_TITLE_LABELS[title.kind], FSP_DISCIPLINE_LABELS[title.discipline]]
    return " ".join(parts)


def profile_strength(
    assessment_score: float | None,
    results: Sequence[FspScoredResult],
    titles: Sequence[FspTitleKind] = (),
) -> float:
    """0–1: 60% the test result for the current grade, up to 40% confirmed FSP history.

    The order inside a category only: the grade and the category come from the test alone, FSP
    results never change them. A candidate who skipped the test only gets the FSP part, so
    self-declared grades rank lower; one without FSP history ranks by the test alone.
    """
    test = TEST_SHARE * assessment_score / 100 if assessment_score is not None else 0.0
    return round(test + fsp_points(results, titles), 4)


# --- facts ---------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CandidateFacts:
    specialization: str | None
    grade: Grade | None
    stack: tuple[str, ...]
    work_formats: tuple[WorkFormat, ...]
    city: str | None
    relocation_ready: bool
    salary_expectation: int | None
    assessment_score: float | None
    fsp: tuple[FspScoredResult, ...]
    # Specializations of the non-priority resumes. They rank below an exact priority match.
    other_specializations: tuple[str, ...] = ()
    fsp_titles: tuple[FspTitleKind, ...] = ()
    # The confirming test was a beta one.
    assessment_beta: bool = False

    @classmethod
    def of(cls, profile: CandidateProfile) -> Self:
        """`profile.fsp_achievements` and `profile.fsp_titles` must be loaded."""
        return cls(
            specialization=profile.specialization,
            grade=profile.grade,
            stack=tuple(profile.stack),
            work_formats=tuple(WorkFormat(value) for value in profile.work_formats),
            city=profile.city,
            relocation_ready=profile.relocation_ready,
            salary_expectation=profile.salary_expectation,
            assessment_score=profile.assessment_score,
            assessment_beta=profile.assessment_beta,
            other_specializations=tuple(
                str(item["specialization"])
                for item in (profile.additional_resumes or [])
                if isinstance(item, dict) and item.get("specialization")
            ),
            fsp=tuple(
                FspScoredResult(
                    event_name=item.event_name,
                    discipline=item.discipline,
                    level=item.level,
                    year=item.year,
                    place=item.place,
                    result=item.result,
                    participation=item.participation,
                    team_name=item.team_name,
                )
                for item in profile.fsp_achievements
            ),
            fsp_titles=tuple(item.kind for item in profile.fsp_titles),
        )

    @property
    def strength(self) -> float:
        return profile_strength(self.assessment_score, self.fsp, self.fsp_titles)


@dataclass(frozen=True, slots=True)
class VacancyFacts:
    specialization: str
    grade: Grade
    stack: tuple[str, ...]
    work_format: WorkFormat
    city: str | None
    salary_from: int
    salary_to: int
    published_at: datetime | None

    @classmethod
    def of(cls, vacancy: Vacancy) -> Self:
        return cls(
            specialization=vacancy.specialization,
            grade=vacancy.grade,
            stack=tuple(vacancy.stack),
            work_format=vacancy.work_format,
            city=vacancy.city,
            salary_from=vacancy.salary_from,
            salary_to=vacancy.salary_to,
            published_at=vacancy.published_at,
        )


# --- fit -----------------------------------------------------------------------------------------

Relation = Literal["same", "related", "other"]
Location = Literal["remote", "same_city", "relocation", "other"]
SalaryFit = Literal["fits", "close", "above", "unknown"]


@dataclass(frozen=True, slots=True)
class Fit:
    # 0–100, rounded half-up to 4 decimals exactly as the Elasticsearch script does.
    points: float
    specialization: Relation
    # Candidate grade minus vacancy grade, in steps; None when the candidate has no grade.
    grade_gap: int | None
    matched_stack: tuple[str, ...]
    stack_size: int
    format_ok: bool
    location: Location
    salary: SalaryFit

    @property
    def score(self) -> float:
        return round(self.points / 100, 4)


def normalize_term(value: str) -> str:
    """Case- and «ё»-insensitive comparison of technologies and cities, as the index does."""
    return value.lower().replace("ё", "е")


def round_points(points: float) -> float:
    """Half-up to 4 decimals: identical in Python and Painless (`Math.floor(x * 10000 + 0.5)`)."""
    return math.floor(points * 10000 + 0.5) / 10000


def _same_city(left: str | None, right: str | None) -> bool:
    return left is not None and right is not None and normalize_term(left) == normalize_term(right)


def _specialization(candidate: CandidateFacts, vacancy: VacancyFacts) -> tuple[float, Relation]:
    if candidate.specialization == vacancy.specialization:
        return WEIGHTS.specialization, "same"
    # A second resume in this profession ranks above a merely related one, below the priority.
    if vacancy.specialization in candidate.other_specializations:
        return WEIGHTS.specialization * SECOND_RESUME_SHARE, "related"
    if candidate.specialization in related_specializations(vacancy.specialization):
        return WEIGHTS.specialization * HALF, "related"
    return 0.0, "other"


def _grade(candidate: CandidateFacts, vacancy: VacancyFacts) -> tuple[float, int | None]:
    if candidate.grade is None:
        return 0.0, None
    gap = GRADES.index(candidate.grade) - GRADES.index(vacancy.grade)
    if gap == 0:
        return WEIGHTS.grade, gap
    return (WEIGHTS.grade * HALF if abs(gap) == 1 else 0.0), gap


def _stack(candidate: CandidateFacts, vacancy: VacancyFacts) -> tuple[float, tuple[str, ...]]:
    owned = {normalize_term(item) for item in candidate.stack}
    matched = tuple(item for item in vacancy.stack if normalize_term(item) in owned)
    if not vacancy.stack:
        return 0.0, matched
    return WEIGHTS.stack * len(matched) / len(vacancy.stack), matched


def _location(candidate: CandidateFacts, vacancy: VacancyFacts) -> tuple[float, Location]:
    if vacancy.work_format == WorkFormat.REMOTE:
        return WEIGHTS.location, "remote"
    if _same_city(candidate.city, vacancy.city):
        return WEIGHTS.location, "same_city"
    if candidate.relocation_ready:
        return WEIGHTS.location * RELOCATION_SHARE, "relocation"
    return 0.0, "other"


def _salary(candidate: CandidateFacts, vacancy: VacancyFacts) -> tuple[float, SalaryFit]:
    expectation = candidate.salary_expectation
    if expectation is None:
        return WEIGHTS.salary * HALF, "unknown"
    if expectation <= vacancy.salary_to:
        return WEIGHTS.salary, "fits"
    if expectation <= vacancy.salary_to * SALARY_TOLERANCE:
        return WEIGHTS.salary * HALF, "close"
    return 0.0, "above"


def fit(candidate: CandidateFacts, vacancy: VacancyFacts, *, bonus: float) -> Fit:
    """How well a candidate and a vacancy suit each other; `bonus` is a 0–1 side-specific signal.

    The additions keep the order of the Elasticsearch script, so both give the same doubles.
    """
    specialization, relation = _specialization(candidate, vacancy)
    grade, gap = _grade(candidate, vacancy)
    stack, matched = _stack(candidate, vacancy)
    format_ok = vacancy.work_format in candidate.work_formats
    location, place = _location(candidate, vacancy)
    salary, salary_fit = _salary(candidate, vacancy)

    points = WEIGHTS.bonus * bonus
    points += specialization
    points += grade
    points += stack
    points += WEIGHTS.work_format if format_ok else 0.0
    points += location
    points += salary
    return Fit(
        points=round_points(points),
        specialization=relation,
        grade_gap=gap,
        matched_stack=matched,
        stack_size=len(vacancy.stack),
        format_ok=format_ok,
        location=place,
        salary=salary_fit,
    )


# Days since publication → freshness bonus for the candidate's feed.
FRESHNESS: tuple[tuple[int, float], ...] = ((3, 1.0), (7, 0.7), (14, 0.4), (30, 0.2))


def as_utc(value: datetime) -> datetime:
    """SQLite returns naive datetimes; every stored datetime is UTC."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def freshness(published_at: datetime | None, now: datetime) -> float:
    if published_at is None:
        return 0.0
    days = (now - as_utc(published_at)).days
    return next((value for limit, value in FRESHNESS if days <= limit), 0.0)


# --- reasons -------------------------------------------------------------------------------------

MAX_REASONS = 5
MAX_LISTED_TECHNOLOGIES = 4


def _plural(count: int, forms: tuple[str, str, str]) -> str:
    """Russian plural: (1 день, 2 дня, 5 дней)."""
    if count % 10 == 1 and count % 100 != 11:  # noqa: PLR2004
        return forms[0]
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:  # noqa: PLR2004
        return forms[1]
    return forms[2]


def rub(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " ₽"


def _technologies(items: Sequence[str], total: int) -> str:
    listed = ", ".join(items[:MAX_LISTED_TECHNOLOGIES])
    return f"{listed} ({len(items)} из {total})"


def _published(published_at: datetime, now: datetime) -> str:
    days = (now - as_utc(published_at)).days
    if days <= 0:
        return "Опубликована сегодня"
    if days == 1:
        return "Опубликована вчера"
    return f"Опубликована {days} {_plural(days, ('день', 'дня', 'дней'))} назад"


def vacancy_reasons(
    candidate: CandidateFacts, vacancy: VacancyFacts, result: Fit, *, now: datetime
) -> list[str]:
    """Why a vacancy is in the candidate's feed, addressed to the candidate."""
    reasons: list[str] = []
    vacancy_grade = GRADE_LABELS[vacancy.grade]
    if result.specialization == "same" and result.grade_gap == 0:
        category = category_for(vacancy.specialization, vacancy.grade)
        reasons.append(f"Ваша категория: {category.label if category else vacancy_grade}")
    else:
        if result.specialization == "related":
            label = SPECIALIZATIONS.get(vacancy.specialization, vacancy.specialization)
            reasons.append(f"Смежная специализация: {label}")
        if result.grade_gap == 1:
            reasons.append(f"Грейд {vacancy_grade} на ступень ниже вашего")
        elif result.grade_gap == -1:
            reasons.append(f"Грейд {vacancy_grade} на ступень выше вашего: шанс вырасти")
    if result.matched_stack:
        reasons.append(f"Совпадает стек: {_technologies(result.matched_stack, result.stack_size)}")
    if result.format_ok:
        reasons.append(f"Подходит формат: {WORK_FORMAT_LABELS[vacancy.work_format].lower()}")
    if result.location == "same_city":
        reasons.append(f"Офис в вашем городе: {vacancy.city}")
    elif result.location == "relocation":
        reasons.append(f"Офис: {vacancy.city}, вы готовы к переезду")
    if result.salary == "fits":
        reasons.append(f"Зарплата до {rub(vacancy.salary_to)} — не ниже ваших ожиданий")
    elif result.salary == "close":
        reasons.append("Зарплата чуть ниже ваших ожиданий")
    if vacancy.published_at is not None:
        reasons.append(_published(vacancy.published_at, now))
    return reasons[:MAX_REASONS]


def _fsp_reason(result: FspScoredResult, title: FspTitleKind | None = None) -> str:
    details = f"{result.event_name} ({FSP_DISCIPLINE_LABELS[result.discipline]}, {result.year})"
    if result.participation == FspParticipation.TEAM:
        details += f", команда «{result.team_name}»" if result.team_name else ", командный зачёт"
    place = f", {result.place}-е место" if result.place is not None else ""
    if result.result == FspOutcome.WINNER:
        text = f"ФСП: победитель — {details}"
    elif result.result == FspOutcome.PRIZEWINNER:
        text = f"ФСП: призёр{place} — {details}"
    elif result.result == FspOutcome.FINALIST:
        text = f"ФСП: финал{place} — {details}"
    else:
        text = f"ФСП: участие — {details}"
    if title is not None:
        text += f"; {FSP_TITLE_LABELS[title]}"
    return text


def _vacancy_fit_reasons(
    candidate: CandidateFacts, vacancy: VacancyFacts, result: Fit
) -> list[str]:
    reasons: list[str] = []
    if result.specialization == "related" and candidate.specialization:
        label = SPECIALIZATIONS.get(candidate.specialization, candidate.specialization)
        reasons.append(f"Смежная специализация: {label}")
    if result.grade_gap in (-1, 1):
        side = "выше" if result.grade_gap == 1 else "ниже"
        reasons.append(f"Грейд на ступень {side} вакансии")
    if result.matched_stack:
        reasons.append(f"Стек вакансии: {_technologies(result.matched_stack, result.stack_size)}")
    if result.format_ok:
        reasons.append(f"Подходит формат: {WORK_FORMAT_LABELS[vacancy.work_format].lower()}")
    if result.location == "same_city":
        reasons.append(f"Город вакансии: {vacancy.city}")
    elif result.location == "relocation":
        reasons.append("Рассматривает переезд")
    expectation = candidate.salary_expectation
    if result.salary == "fits" and expectation is not None:
        reasons.append(f"Ожидания {rub(expectation)} — в пределах вилки")
    elif result.salary == "close" and expectation is not None:
        reasons.append(f"Ожидания {rub(expectation)} — чуть выше вилки")
    return reasons


def candidate_reasons(
    candidate: CandidateFacts,
    result: Fit | None,
    *,
    vacancy: VacancyFacts | None = None,
    stack_filter: Sequence[str] = (),
) -> list[str]:
    """Why a candidate is in the recruiter's feed. Grammatically neutral: no gender is stored."""
    reasons: list[str] = []
    if candidate.assessment_score is not None:
        beta = ", тест в бета-версии" if candidate.assessment_beta else ""
        reasons.append(f"Грейд подтверждён тестом: {candidate.assessment_score:.0f} из 100{beta}")
    else:
        reasons.append("Грейд указан без теста")
    best = best_fsp_result(candidate.fsp)
    title = best_fsp_title(candidate.fsp_titles)
    if best is not None:
        reasons.append(_fsp_reason(best, title))
    elif title is not None:
        reasons.append(f"ФСП: {FSP_TITLE_LABELS[title]}")

    if result is not None and vacancy is not None:
        reasons += _vacancy_fit_reasons(candidate, vacancy, result)
    elif stack_filter:
        owned = {normalize_term(item) for item in candidate.stack}
        matched = [item for item in stack_filter if normalize_term(item) in owned]
        if matched:
            reasons.append(f"Стек: {', '.join(matched[:MAX_LISTED_TECHNOLOGIES])}")
    return reasons[:MAX_REASONS]
