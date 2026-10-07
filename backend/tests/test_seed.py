from collections import Counter
from statistics import median

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.models import CandidateProfile, Company, FspAchievement, Grade, User, UserRole, Vacancy
from app.seed.fixtures import DATA_DIR, SeedData, load_seed_data
from app.seed.generate import (
    DEMO_CANDIDATE_EMAIL,
    DEMO_EMPLOYER2_EMAIL,
    DEMO_EMPLOYER_EMAIL,
    EXPERIENCE_YEARS,
    build_dataset,
    dump,
)
from app.seed.loader import SeedConflictError, demo_data_loaded, seed_database, seed_id
from app.services.categories import SPECIALIZATIONS
from app.services.inn import is_valid_inn
from tests.conftest import API, PASSWORD

GRADE_ORDER = list(Grade)


@pytest.fixture(scope="module")
def data() -> SeedData:
    return load_seed_data()


async def _count(session: AsyncSession, model: type[object]) -> int:
    return await session.scalar(select(func.count()).select_from(model)) or 0


def test_committed_json_matches_the_generator() -> None:
    for name, records in build_dataset().items():
        committed = (DATA_DIR / f"{name}.json").read_text("utf-8")
        assert committed == dump(records), (
            f"{name}.json is stale: uv run python -m app.seed.generate"
        )


def test_every_category_has_candidates_and_vacancies(data: SeedData) -> None:
    assert len(data.candidates) >= 100
    assert len(data.companies) == 20
    visible = [candidate for candidate in data.candidates if candidate.is_visible_to_employers]
    published = [vacancy for vacancy in data.vacancies if vacancy.published_days_ago is not None]

    assert {candidate.specialization for candidate in visible} == set(SPECIALIZATIONS)
    assert {candidate.grade for candidate in visible} == set(Grade)
    assert {vacancy.specialization for vacancy in published} == set(SPECIALIZATIONS)
    assert {vacancy.grade for vacancy in published} == set(Grade)
    assert min(Counter(vacancy.company_key for vacancy in data.vacancies).values()) >= 3


def test_dataset_contains_the_edge_cases(data: SeedData) -> None:
    candidates = data.candidates
    # ТЗ: a profile without FSP history must be handled explicitly.
    assert any(candidate.fsp_member_id is None for candidate in candidates)
    assert any(
        candidate.fsp_member_id and not candidate.fsp_achievements for candidate in candidates
    )
    assert any(candidate.assessment_score is None for candidate in candidates)
    assert any(not candidate.is_visible_to_employers for candidate in candidates)
    assert any(vacancy.published_days_ago is None for vacancy in data.vacancies)


def test_grades_are_consistent_with_experience_and_salary(data: SeedData) -> None:
    for candidate in data.candidates:
        low, high = EXPERIENCE_YEARS[candidate.grade]
        assert low <= candidate.experience_years <= high, candidate.key

    def medians(values: dict[Grade, list[int]]) -> list[float]:
        return [median(values[grade]) for grade in GRADE_ORDER]

    expected: dict[Grade, list[int]] = {grade: [] for grade in Grade}
    offered: dict[Grade, list[int]] = {grade: [] for grade in Grade}
    for candidate in data.candidates:
        expected[candidate.grade].append(candidate.salary_expectation)
    for vacancy in data.vacancies:
        offered[vacancy.grade].append((vacancy.salary_from + vacancy.salary_to) // 2)
    assert medians(expected) == sorted(medians(expected))
    assert medians(offered) == sorted(medians(offered))


async def test_seeding_twice_keeps_one_copy(
    sessionmaker: async_sessionmaker[AsyncSession], data: SeedData
) -> None:
    for _ in range(2):
        async with sessionmaker() as session:
            summary = await seed_database(session, data, password_hash="not-a-real-hash")
            await session.commit()

    async with sessionmaker() as session:
        assert await _count(session, User) == len(data.companies) + len(data.candidates)
        assert await _count(session, Company) == summary.companies == len(data.companies)
        assert await _count(session, Vacancy) == summary.vacancies == len(data.vacancies)
        assert await _count(session, CandidateProfile) == summary.candidates
        assert await _count(session, FspAchievement) == summary.fsp_achievements > 0

        demo = await session.scalar(
            select(CandidateProfile)
            .where(CandidateProfile.id == seed_id("candidate", data.candidates[0].key))
            .options(selectinload(CandidateProfile.fsp_achievements))
        )
        assert demo is not None
        assert demo.fsp_member_id is not None
        assert len(demo.fsp_achievements) == len(data.candidates[0].fsp_achievements)
        assert demo.employment_types
        assert demo.last_active_at is not None


async def test_demo_rows_have_the_registration_fields(
    sessionmaker: async_sessionmaker[AsyncSession], data: SeedData
) -> None:
    async with sessionmaker() as session:
        await seed_database(session, data, password_hash="not-a-real-hash")
        await session.commit()

    async with sessionmaker() as session:
        companies = list(await session.scalars(select(Company)))
        accredited = [company for company in companies if company.it_accredited]
        assert seed_id("company", data.companies[0].key) in {item.id for item in accredited}
        assert 0 < len(accredited) < len(companies)
        assert all(is_valid_inn(company.inn or "") for company in companies)

        vacancies = list(await session.scalars(select(Vacancy)))
        for vacancy in vacancies:
            assert vacancy.grades[0] == vacancy.grade
            assert vacancy.stack_required + vacancy.stack_nice == vacancy.stack
            assert vacancy.employment_types
        assert any(len(vacancy.grades) == 2 for vacancy in vacancies)

        profiles = list(await session.scalars(select(CandidateProfile)))
        for profile in profiles:
            assert profile.is_visible_to_employers == (profile.job_status != "not_looking")
            assert profile.no_experience == (profile.experience_years == 0)


async def test_demo_accounts_can_sign_in(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], data: SeedData
) -> None:
    async with sessionmaker() as session:
        await seed_database(session, data, password_hash=hash_password(PASSWORD))
        await session.commit()

    for email, role in (
        (DEMO_CANDIDATE_EMAIL, "candidate"),
        (DEMO_EMPLOYER_EMAIL, "employer"),
        (DEMO_EMPLOYER2_EMAIL, "employer"),
    ):
        response = await client.post(
            f"{API}/auth/login", json={"email": email, "password": PASSWORD}
        )
        assert response.status_code == 200, response.text
        assert response.json()["user"]["role"] == role


async def test_seed_does_not_take_over_existing_accounts(
    sessionmaker: async_sessionmaker[AsyncSession], data: SeedData
) -> None:
    async with sessionmaker() as session:
        session.add(User(email=DEMO_EMPLOYER_EMAIL, password_hash="x", role=UserRole.EMPLOYER))
        await session.commit()

    async with sessionmaker() as session:
        with pytest.raises(SeedConflictError, match=DEMO_EMPLOYER_EMAIL):
            await seed_database(session, data, password_hash="not-a-real-hash")


async def test_demo_data_loaded_detects_an_earlier_load(
    sessionmaker: async_sessionmaker[AsyncSession], data: SeedData
) -> None:
    async with sessionmaker() as session:
        assert not await demo_data_loaded(session, data)
        await seed_database(session, data, password_hash="not-a-real-hash")
        await session.commit()
    async with sessionmaker() as session:
        assert await demo_data_loaded(session, data)
