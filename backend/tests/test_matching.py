from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.models import FspDiscipline, FspEventLevel, Grade, WorkFormat
from app.models.enums import FspOutcome, FspParticipation, FspTitleKind
from app.search.base import CandidateSearchQuery
from app.search.query import build_search_body
from app.services.matching import (
    WEIGHTS,
    CandidateFacts,
    FspScoredResult,
    VacancyFacts,
    candidate_reasons,
    fit,
    freshness,
    fsp_points,
    profile_strength,
    vacancy_reasons,
)

NOW = datetime(2026, 10, 6, tzinfo=UTC)


CANDIDATE = CandidateFacts(
    specialization="backend",
    grade=Grade.MIDDLE,
    stack=("Python", "PostgreSQL", "FastAPI", "Kafka"),
    work_formats=(WorkFormat.REMOTE, WorkFormat.HYBRID),
    city="Москва",
    relocation_ready=False,
    salary_expectation=250_000,
    assessment_score=90.0,
    fsp=(),
)

VACANCY = VacancyFacts(
    specialization="backend",
    grade=Grade.MIDDLE,
    stack=("Python", "postgresql", "Redis", "Kafka"),
    work_format=WorkFormat.REMOTE,
    city=None,
    salary_from=200_000,
    salary_to=300_000,
    published_at=NOW - timedelta(days=1),
)


def candidate(**changes: Any) -> CandidateFacts:
    return replace(CANDIDATE, **changes)


def vacancy(**changes: Any) -> VacancyFacts:
    return replace(VACANCY, **changes)


def test_profile_strength_combines_test_and_fsp() -> None:
    national_win = FspScoredResult.placed(
        "Кубок России", FspDiscipline.PRODUCT, FspEventLevel.NATIONAL, 2025, 1
    )
    participation = FspScoredResult.placed(
        "Чемпионат Москвы", FspDiscipline.PRODUCT, FspEventLevel.REGIONAL, 2024, None
    )

    assert profile_strength(None, ()) == 0
    assert profile_strength(100.0, ()) == 0.6
    assert profile_strength(None, (national_win,)) == 0.38
    # The best result counts, every further one adds a little; the FSP part is capped at 0.4.
    assert profile_strength(80.0, (national_win, participation)) == 0.88
    assert profile_strength(100.0, (national_win,) * 5) == 1.0


def test_fsp_points_weigh_result_team_and_title() -> None:
    prize = FspScoredResult.placed(
        "Кубок России", FspDiscipline.ALGORITHMIC, FspEventLevel.NATIONAL, 2025, 3
    )
    team_prize = replace(prize, participation=FspParticipation.TEAM, team_name="NullPointer")
    unplaced_prize = replace(prize, place=None, result=FspOutcome.PRIZEWINNER)

    assert fsp_points((prize,)) == 0.32
    # A team result is shared with teammates; a prizewinner without a place counts as 2nd.
    assert fsp_points((team_prize,)) == pytest.approx(0.288)
    assert fsp_points((unplaced_prize,)) == 0.35
    # The highest title adds to the results, and a title alone still counts.
    assert fsp_points((prize,), (FspTitleKind.RANK_2, FspTitleKind.KMS)) == pytest.approx(0.35)
    assert fsp_points((), (FspTitleKind.RANK_1,)) == 0.02
    assert fsp_points((prize,) * 6, (FspTitleKind.ZMS,)) == 0.4


def test_fsp_orders_inside_a_category_and_never_sets_it() -> None:
    win = FspScoredResult.placed(
        "Чемпионат России", FspDiscipline.ALGORITHMIC, FspEventLevel.NATIONAL, 2025, 1
    )
    plain = candidate(assessment_score=70.0)
    champion = candidate(assessment_score=70.0, fsp=(win,), fsp_titles=(FspTitleKind.KMS,))

    assert champion.strength > plain.strength
    # Neither the grade nor the category depend on FSP: only the order inside it.
    assert (champion.grade, champion.specialization) == (plain.grade, plain.specialization)
    # Without FSP history the candidate ranks by the test alone.
    assert plain.strength == profile_strength(70.0, ())
    assert candidate_reasons(plain, None) == ["Грейд подтверждён тестом: 70 из 100"]


def test_perfect_fit_and_its_parts() -> None:
    result = fit(candidate(), vacancy(), bonus=1.0)

    # Case-insensitive stack: 3 of 4 technologies (no Redis).
    assert result.matched_stack == ("Python", "postgresql", "Kafka")
    expected = (
        WEIGHTS.bonus
        + WEIGHTS.specialization
        + WEIGHTS.grade
        + WEIGHTS.stack * 3 / 4
        + WEIGHTS.work_format
        + WEIGHTS.location
        + WEIGHTS.salary
    )
    assert result.points == expected
    assert (result.specialization, result.grade_gap, result.salary) == ("same", 0, "fits")


def test_partial_credit() -> None:
    related = fit(candidate(specialization="fullstack"), vacancy(), bonus=0)
    senior_job = fit(candidate(), vacancy(grade=Grade.SENIOR), bonus=0)
    far_grade = fit(candidate(grade=Grade.INTERN), vacancy(grade=Grade.SENIOR), bonus=0)
    office_elsewhere = fit(
        candidate(relocation_ready=True),
        vacancy(work_format=WorkFormat.OFFICE, city="Казань"),
        bonus=0,
    )
    expensive = fit(candidate(salary_expectation=320_000), vacancy(), bonus=0)
    unaffordable = fit(candidate(salary_expectation=500_000), vacancy(), bonus=0)

    assert related.specialization == "related"
    assert senior_job.grade_gap == -1
    assert far_grade.grade_gap == -3
    assert (office_elsewhere.location, office_elsewhere.format_ok) == ("relocation", False)
    assert (expensive.salary, unaffordable.salary) == ("close", "above")
    assert fit(candidate(), vacancy(), bonus=0).points > senior_job.points > far_grade.points


def test_freshness_decays() -> None:
    assert freshness(NOW, NOW) == 1.0
    assert freshness(NOW - timedelta(days=10), NOW) == 0.4
    assert freshness(NOW - timedelta(days=90), NOW) == 0.0
    assert freshness(None, NOW) == 0.0


def test_reasons_explain_the_position() -> None:
    facts = candidate(
        fsp=(
            FspScoredResult.placed(
                "Кубок России", FspDiscipline.SECURITY, FspEventLevel.NATIONAL, 2025, 2
            ),
        )
    )
    team_win = FspScoredResult.placed(
        "Хакатон ФСП",
        FspDiscipline.PRODUCT,
        FspEventLevel.NATIONAL,
        2026,
        1,
        participation=FspParticipation.TEAM,
        team_name="Сибирский код",
    )
    titled = candidate(fsp=(team_win,), fsp_titles=(FspTitleKind.KMS,))
    job = vacancy()
    result = fit(facts, job, bonus=facts.strength)

    for_candidate = vacancy_reasons(facts, job, result, now=NOW)
    for_employer = candidate_reasons(facts, result, vacancy=job)
    untested = candidate_reasons(candidate(assessment_score=None), None)

    assert for_candidate[0] == "Ваша категория: Backend-разработка · Middle"
    assert "Совпадает стек: Python, postgresql, Kafka (3 из 4)" in for_candidate
    assert for_candidate[-1] == "Опубликована вчера"
    assert for_employer[:2] == [
        "Грейд подтверждён тестом: 90 из 100",
        "ФСП: призёр, 2-е место — Кубок России (программирование систем ИБ, 2025)",
    ]
    assert untested == ["Грейд указан без теста"]
    assert candidate_reasons(titled, None)[1] == (
        "ФСП: победитель — Хакатон ФСП (продуктовое программирование, 2026), "
        "команда «Сибирский код»; КМС"
    )


def test_elasticsearch_query_mirrors_filters_and_fit() -> None:
    job = vacancy(work_format=WorkFormat.HYBRID, city="Москва")
    body = build_search_body(
        CandidateSearchQuery(
            specialization="backend",
            grades=(Grade.MIDDLE, Grade.SENIOR),
            stack=("Python", "Kafka"),
            has_fsp=True,
            city="Москва",
            vacancy=job,
            exclude_ids=(),
        ),
        offset=20,
        limit=10,
    )

    scored = body["query"]["function_score"]
    filters = scored["query"]["bool"]["filter"]
    params = scored["script_score"]["script"]["params"]
    assert {"term": {"visible": True}} in filters
    assert {"terms": {"grade": ["middle", "senior"]}} in filters
    assert {"term": {"stack": "Python"}} in filters
    assert {"term": {"stack": "Kafka"}} in filters
    assert params["stack"] == ["python", "postgresql", "redis", "kafka"]
    assert params["city"] == "москва"
    assert params["related"] == ["data-engineering", "fullstack"]
    assert params["w_stack"] == WEIGHTS.stack
    assert body["sort"] == [{"_score": "desc"}, {"profile_strength": "desc"}, {"id": "asc"}]
    assert (body["from"], body["size"], body["track_total_hits"]) == (20, 10, True)


def test_elasticsearch_query_without_vacancy_ranks_by_profile_strength() -> None:
    plain = build_search_body(CandidateSearchQuery(), offset=0, limit=20)
    text = build_search_body(CandidateSearchQuery(text="сеньор питон"), offset=0, limit=20)
    by_salary = build_search_body(CandidateSearchQuery(sort="salary"), offset=0, limit=20)

    assert plain["sort"] == [{"profile_strength": "desc"}, {"id": "asc"}]
    assert "function_score" in text["query"]
    assert by_salary["sort"][0] == {"salary_expectation": {"order": "asc", "missing": "_last"}}
