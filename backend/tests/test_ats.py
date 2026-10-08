"""Employer ATS poll: our filters, one screening per event, the candidate bank stays unchanged."""

from httpx import AsyncClient

from app.integrations.ats.normalized import NormalizedCandidate, NormalizedJob
from app.services.ats_pipeline import HardFilters, ScoreRules, ScreeningPipeline, default_pipeline
from tests.conftest import API, bearer, register_and_login
from tests.test_vacancies import employer_with_company


async def test_poll_screens_once_and_leaves_platform_candidates_alone(client: AsyncClient) -> None:
    token = await employer_with_company(client, "ats-hr@fsp.ru", inn="7707083893")
    headers = bearer(token)

    missing = await client.post(f"{API}/ats/poll", headers=headers)
    assert missing.status_code == 404

    connected = await client.post(f"{API}/ats/connection", headers=headers)
    assert connected.status_code == 201, connected.text
    assert connected.json()["provider"] == "mock"

    first = await client.post(f"{API}/ats/poll", headers=headers)
    assert first.status_code == 200, first.text
    assert first.json() == {"ingested": 3, "screened": 3}

    second = await client.post(f"{API}/ats/poll", headers=headers)
    assert second.json() == {"ingested": 0, "screened": 0}

    listed = await client.get(f"{API}/ats/applications", headers=headers)
    assert listed.status_code == 200, listed.text
    by_name = {item["candidateName"]: item for item in listed.json()}
    assert by_name["Мария Соколова"]["decision"] == "pass"
    assert by_name["Мария Соколова"]["synced"] is True
    assert by_name["Илья Орлов"]["decision"] == "reject"
    assert "PostgreSQL" in by_name["Кирилл Панков"]["missingSkills"]
    assert by_name["Кирилл Панков"]["decision"] == "reject"

    bank = await client.get(f"{API}/candidates", headers=headers)
    assert bank.status_code == 200
    assert all(item["displayName"] not in by_name for item in bank.json()["items"])


async def test_candidate_cannot_open_ats(client: AsyncClient) -> None:
    token = await register_and_login(client, "ats-dev@fsp.ru")
    denied = await client.get(f"{API}/ats/applications", headers=bearer(token))
    assert denied.status_code == 403


def test_null_stages_do_not_change_the_score() -> None:
    candidate = NormalizedCandidate(
        external_id="p",
        name="Мария",
        skills=("Python", "PostgreSQL"),
        experience_years=5,
        city="Москва",
        salary_expectation=250_000,
    )
    job = NormalizedJob(
        external_id="j",
        title="Бэкенд",
        required_skills=("Python", "PostgreSQL"),
        salary_from=200_000,
        salary_to=320_000,
        city="Москва",
    )
    full = default_pipeline().run(candidate, job)
    bare = ScreeningPipeline((HardFilters(), ScoreRules())).run(candidate, job)
    assert full.score == bare.score == 100
    assert full.decision == bare.decision
    assert full.model_version == "rules-1"
