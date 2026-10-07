from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.vacancy import VacancyCreate
from app.services.age import age_on, experience_years
from app.services.inn import is_valid_inn


def test_inn_check_digits() -> None:
    assert is_valid_inn("7707083893")
    assert is_valid_inn("500100732259")
    assert not is_valid_inn("7707083890")
    assert not is_valid_inn("500100732250")
    assert not is_valid_inn("77070838")
    assert not is_valid_inn("77070838９3")


def test_age_turns_on_the_birthday() -> None:
    birth = date(2010, 6, 15)
    assert age_on(birth, date(2024, 6, 14)) == 13
    assert age_on(birth, date(2024, 6, 15)) == 14


def test_experience_counts_overlapping_jobs_once() -> None:
    today = date(2025, 1, 10)
    assert experience_years([("2019-01", "2021-12"), ("2021-06", "2022-12")], today) == 4
    assert experience_years([("2023-01", None)], today) == 2
    assert experience_years([], today) == 0


VACANCY = {
    "title": "Backend-разработчик",
    "description": "Пишем платёжный шлюз. " * 10,
    "specialization": "backend",
    "grades": ["junior", "middle"],
    "stackRequired": ["Python"],
    "salary": {"from": 150000, "to": 200000},
    "workFormat": "hybrid",
    "city": "Томск",
    "employmentTypes": ["full"],
}


def test_vacancy_contract_rules() -> None:
    assert VacancyCreate.model_validate(VACANCY).verified_grade_only is True
    with pytest.raises(ValidationError):
        VacancyCreate.model_validate({**VACANCY, "grades": ["junior", "senior"]})
    with pytest.raises(ValidationError):
        VacancyCreate.model_validate({**VACANCY, "city": None})
    with pytest.raises(ValidationError):
        VacancyCreate.model_validate({**VACANCY, "minExperienceYears": 2})
    assert VacancyCreate.model_validate({**VACANCY, "workFormat": "remote", "city": None})
