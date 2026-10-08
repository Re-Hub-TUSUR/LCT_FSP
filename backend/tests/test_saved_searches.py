import json
import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import hash_password
from app.models import CandidateProfile, Grade, Vacancy, WorkFormat
from app.seed.fixtures import SeedData, load_seed_data
from app.seed.generate import DEMO_CANDIDATE_EMAIL, DEMO_EMPLOYER_EMAIL
from app.seed.loader import seed_database
from app.services.notifications import NotificationHub
from app.services.saved_searches import announce_new_results
from tests.conftest import API, PASSWORD, bearer, login


@pytest.fixture
async def data(sessionmaker: async_sessionmaker[AsyncSession]) -> SeedData:
    data = load_seed_data()
    async with sessionmaker() as session:
        await seed_database(session, data, password_hash=hash_password(PASSWORD))
        await session.commit()
    return data


async def call(client: AsyncClient, method: str, path: str, token: str, **kwargs: Any) -> Any:
    response = await client.request(method, f"{API}{path}", headers=bearer(token), **kwargs)
    assert response.status_code < 300, response.text
    return response.json() if response.content else None


BACKEND_MIDDLE = {"specializations": ["backend"], "grades": ["middle"]}


async def test_saved_candidate_search_counts_new_candidates_and_alerts_once(
    client: AsyncClient, data: SeedData, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    token = await login(client, DEMO_EMPLOYER_EMAIL)
    saved = await call(
        client, "POST", "/candidates/saved-searches", token, json={"filters": BACKEND_MIDDLE}
    )
    found = await call(
        client, "GET", "/candidates", token, params={"specialization": "backend", "grade": "middle"}
    )

    assert saved["title"] == "Backend-разработка · Middle"
    assert saved["count"] == found["total"] > 0
    assert saved["newCount"] == 0

    # A frontend developer retrains: now the search finds one more candidate.
    async with sessionmaker() as session:
        profile = await session.scalar(
            select(CandidateProfile).where(
                CandidateProfile.specialization == "frontend",
                CandidateProfile.is_visible_to_employers.is_(True),
            )
        )
        assert profile is not None
        profile.specialization = "backend"
        profile.grade = Grade.MIDDLE
        await session.commit()

    [listed] = await call(client, "GET", "/candidates/saved-searches", token)
    assert (listed["count"], listed["newCount"]) == (saved["count"] + 1, 1)

    hub = NotificationHub()
    employer = (await call(client, "GET", "/users/me", token))["id"]
    queue = hub.subscribe(uuid.UUID(employer))
    assert await announce_new_results(sessionmaker, hub, None) == 1
    event = json.loads(queue.get_nowait())
    assert event == {
        "type": "saved_search_new",
        "searchId": saved["id"],
        "kind": "candidates",
        "title": "Backend-разработка · Middle",
        "count": 1,
    }
    # Every new result is announced once.
    assert await announce_new_results(sessionmaker, hub, None) == 0

    opened = await call(client, "POST", f"/candidates/saved-searches/{saved['id']}/seen", token)
    assert (opened["count"], opened["newCount"]) == (listed["count"], 0)


async def test_saved_vacancy_search_counts_new_vacancies(
    client: AsyncClient, data: SeedData, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    token = await login(client, DEMO_CANDIDATE_EMAIL)
    body = {"mode": "free", "filters": {"workFormats": ["remote"], "salaryMin": 300_000}}
    saved = await call(client, "POST", "/vacancies/feed/saved-searches", token, json=body)
    feed = await call(
        client,
        "GET",
        "/vacancies/feed",
        token,
        params={"mode": "free", "workFormat": "remote", "salaryMin": 300_000},
    )

    # Sums keep their digits together: non-breaking spaces.
    assert saved["title"] == "Удалённо · от 300 000 ₽"
    assert saved["summary"] == "все вакансии"
    assert saved["count"] == feed["total"]

    # An office vacancy goes remote and pays more: it is new for the search.
    async with sessionmaker() as session:
        vacancy = await session.scalar(
            select(Vacancy).where(
                Vacancy.work_format == WorkFormat.OFFICE, Vacancy.published_at.is_not(None)
            )
        )
        assert vacancy is not None
        vacancy.work_format = WorkFormat.REMOTE
        vacancy.city = None
        vacancy.salary_to = 400_000
        await session.commit()

    [listed] = await call(client, "GET", "/vacancies/feed/saved-searches", token)
    assert (listed["count"], listed["newCount"]) == (saved["count"] + 1, 1)


async def test_saved_searches_are_private_and_deletable(
    client: AsyncClient, data: SeedData
) -> None:
    employer = await login(client, DEMO_EMPLOYER_EMAIL)
    candidate = await login(client, DEMO_CANDIDATE_EMAIL)
    saved = await call(client, "POST", "/vacancies/feed/saved-searches", candidate, json={})

    foreign = await client.post(
        f"{API}/candidates/saved-searches/{saved['id']}/seen", headers=bearer(employer)
    )
    assert foreign.status_code == 404
    await call(client, "DELETE", f"/vacancies/feed/saved-searches/{saved['id']}", candidate)
    assert await call(client, "GET", "/vacancies/feed/saved-searches", candidate) == []


async def test_no_saved_searches_no_alerts(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    assert await announce_new_results(sessionmaker, NotificationHub(), None) == 0
