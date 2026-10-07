from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import hash_password
from app.seed.fixtures import SeedData, load_seed_data
from app.seed.generate import DEMO_CANDIDATE_EMAIL, DEMO_EMPLOYER_EMAIL
from app.seed.loader import seed_database, seed_id
from tests.conftest import API, PASSWORD, bearer, login, register_and_login

# Far enough from the demo meetings the seed puts into the coming days.
SLOT = (datetime.now(UTC) + timedelta(days=30)).replace(hour=9, minute=0, second=0, microsecond=0)


@pytest.fixture
async def data(sessionmaker: async_sessionmaker[AsyncSession]) -> SeedData:
    data = load_seed_data()
    async with sessionmaker() as session:
        await seed_database(session, data, password_hash=hash_password(PASSWORD))
        await session.commit()
    return data


def meeting(
    candidate_id: Any, starts_at: datetime = SLOT, minutes: int = 60, **extra: Any
) -> dict[str, Any]:
    return {
        "candidateId": str(candidate_id),
        "title": "Техническое интервью",
        "startsAt": starts_at.isoformat(),
        "endsAt": (starts_at + timedelta(minutes=minutes)).isoformat(),
        **extra,
    }


async def events(client: AsyncClient, token: str, around: datetime = SLOT) -> list[dict[str, Any]]:
    response = await client.get(
        f"{API}/calendar/events",
        params={
            "from": (around - timedelta(days=1)).isoformat(),
            "to": (around + timedelta(days=1)).isoformat(),
        },
        headers=bearer(token),
    )
    assert response.status_code == 200, response.text
    items: list[dict[str, Any]] = response.json()
    return items


async def test_employer_schedules_and_candidate_confirms(
    client: AsyncClient, data: SeedData
) -> None:
    employer = await login(client, DEMO_EMPLOYER_EMAIL)
    candidate = await login(client, DEMO_CANDIDATE_EMAIL)
    candidate_id = seed_id("candidate", data.candidates[0].key)
    vacancy_id = seed_id("vacancy", "payflow-02")

    created = await client.post(
        f"{API}/calendar/events",
        json=meeting(candidate_id, vacancyId=str(vacancy_id), location=" https://meet.example/1 "),
        headers=bearer(employer),
    )
    assert created.status_code == 201, created.text
    event = created.json()
    assert event["kind"] == "interview"
    assert event["status"] == "pending"
    assert event["company"]["name"] == "ПэйФлоу"
    assert event["candidate"] == {
        "id": str(candidate_id),
        "name": data.candidates[0].display_name,
    }
    assert event["vacancy"]["id"] == str(vacancy_id)
    assert event["location"] == "https://meet.example/1"

    assert [item["id"] for item in await events(client, employer)] == [event["id"]]
    seen = await events(client, candidate)
    assert [item["id"] for item in seen] == [event["id"]]
    assert datetime.fromisoformat(seen[0]["startsAt"]) == SLOT

    confirmed = await client.post(
        f"{API}/calendar/events/{event['id']}/confirm", headers=bearer(candidate)
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "confirmed"
    assert (await events(client, employer))[0]["status"] == "confirmed"


async def test_moving_a_meeting_asks_the_candidate_again(
    client: AsyncClient, data: SeedData
) -> None:
    employer = await login(client, DEMO_EMPLOYER_EMAIL)
    candidate = await login(client, DEMO_CANDIDATE_EMAIL)
    candidate_id = seed_id("candidate", data.candidates[0].key)
    created = await client.post(
        f"{API}/calendar/events", json=meeting(candidate_id), headers=bearer(employer)
    )
    event_id = created.json()["id"]
    await client.post(f"{API}/calendar/events/{event_id}/decline", headers=bearer(candidate))

    body = meeting(candidate_id, SLOT + timedelta(hours=3), note="Перенесли на после обеда")
    del body["candidateId"]
    moved = await client.put(
        f"{API}/calendar/events/{event_id}", json=body, headers=bearer(employer)
    )

    assert moved.status_code == 200, moved.text
    assert moved.json()["status"] == "pending"
    assert moved.json()["note"] == "Перенесли на после обеда"
    assert datetime.fromisoformat(moved.json()["startsAt"]) == SLOT + timedelta(hours=3)

    cancelled = await client.delete(f"{API}/calendar/events/{event_id}", headers=bearer(employer))
    assert cancelled.status_code == 204
    assert await events(client, candidate) == []


async def test_slot_rules(client: AsyncClient, data: SeedData) -> None:
    employer = await login(client, DEMO_EMPLOYER_EMAIL)
    visible = [c for c in data.candidates if c.is_visible_to_employers]
    first, second = (seed_id("candidate", c.key) for c in visible[:2])
    hidden = next(c for c in data.candidates if not c.is_visible_to_employers)

    async def post(body: dict[str, Any]) -> int:
        response = await client.post(f"{API}/calendar/events", json=body, headers=bearer(employer))
        return response.status_code

    assert await post(meeting(first)) == 201
    # Overlaps the first one by half an hour.
    assert await post(meeting(second, SLOT + timedelta(minutes=30))) == 409
    # Back to back is fine.
    assert await post(meeting(second, SLOT + timedelta(hours=1))) == 201
    assert await post(meeting(first, datetime.now(UTC) - timedelta(hours=2))) == 400
    assert await post(meeting(first, SLOT + timedelta(days=1), minutes=0)) == 422
    assert await post(meeting(first, SLOT + timedelta(days=1), minutes=9 * 60)) == 422
    assert await post(meeting(seed_id("candidate", hidden.key), SLOT + timedelta(days=2))) == 404
    foreign_vacancy = str(seed_id("vacancy", "korzinka-01"))
    assert await post(meeting(first, SLOT + timedelta(days=2), vacancyId=foreign_vacancy)) == 404


async def test_meetings_are_private_to_their_sides(client: AsyncClient, data: SeedData) -> None:
    employer = await login(client, DEMO_EMPLOYER_EMAIL)
    candidate = await login(client, DEMO_CANDIDATE_EMAIL)
    stranger = await register_and_login(client, "stranger@fsp.ru")
    rival = await register_and_login(client, "rival@fsp.ru", role="employer")
    candidate_id = seed_id("candidate", data.candidates[0].key)
    created = await client.post(
        f"{API}/calendar/events", json=meeting(candidate_id), headers=bearer(employer)
    )
    event_id = created.json()["id"]
    body = meeting(candidate_id)

    assert await events(client, stranger) == []
    assert await events(client, rival) == []
    by_candidate = await client.post(f"{API}/calendar/events", json=body, headers=bearer(candidate))
    by_rival = await client.delete(f"{API}/calendar/events/{event_id}", headers=bearer(rival))
    by_stranger = await client.post(
        f"{API}/calendar/events/{event_id}/confirm", headers=bearer(stranger)
    )
    by_employer = await client.post(
        f"{API}/calendar/events/{event_id}/confirm", headers=bearer(employer)
    )
    without_company = await client.post(f"{API}/calendar/events", json=body, headers=bearer(rival))

    assert by_candidate.status_code == by_employer.status_code == 403
    assert by_rival.status_code == by_stranger.status_code == 404
    assert without_company.status_code == 409


async def test_seed_puts_demo_meetings_into_both_calendars(
    client: AsyncClient, data: SeedData
) -> None:
    employer = await login(client, DEMO_EMPLOYER_EMAIL)
    candidate = await login(client, DEMO_CANDIDATE_EMAIL)
    week = {
        "from": datetime.now(UTC).isoformat(),
        "to": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
    }

    company = await client.get(f"{API}/calendar/events", params=week, headers=bearer(employer))
    own = await client.get(f"{API}/calendar/events", params=week, headers=bearer(candidate))

    assert len(company.json()) == 3
    assert len(own.json()) == 1
    starts = [item["startsAt"] for item in company.json()]
    assert starts == sorted(starts)
