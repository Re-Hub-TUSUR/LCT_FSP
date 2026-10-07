"""Time a candidate spends on every task of an attempt."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import AssessmentAttempt, AssessmentTaskTime
from tests.conftest import API, bearer, register_and_login
from tests.test_assessments import platform_test, start


async def test_time_is_summed_per_task_and_capped(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    # Quiz only: no code runner is needed.
    await platform_test(client, sessionmaker, with_code=False)
    token = await register_and_login(client, "dev@fsp.ru")
    attempt = await start(client, token)
    first, second = (task["id"] for task in attempt["tasks"])
    url = f"{API}/assessments/attempts/{attempt['id']}/time"
    # The attempt has been going for ten minutes: the cap below is the attempt's age.
    async with sessionmaker() as session:
        row = await session.get(AssessmentAttempt, uuid.UUID(attempt["id"]))
        assert row is not None
        row.started_at = datetime.now(UTC) - timedelta(minutes=10)
        await session.commit()

    for task_id, seconds in ((first, 0.4), (second, 0.3), (first, 0.2)):
        response = await client.post(
            url, headers=bearer(token), json={"taskId": task_id, "seconds": seconds}
        )
        assert response.status_code == 204, response.text
    # More than the attempt has lasted is cut to the attempt's age.
    long = await client.post(url, headers=bearer(token), json={"taskId": second, "seconds": 3000})
    assert long.status_code == 204

    async with sessionmaker() as session:
        rows = {
            str(row.task_id): row.seconds
            for row in await session.scalars(select(AssessmentTaskTime))
        }
    assert rows[first] == 0.6
    assert 590 < rows[second] <= 601

    foreign = await client.post(
        url, headers=bearer(token), json={"taskId": str(uuid.uuid4()), "seconds": 1}
    )
    other = await register_and_login(client, "other@fsp.ru")
    stranger = await client.post(url, headers=bearer(other), json={"taskId": first, "seconds": 1})
    zero = await client.post(url, headers=bearer(token), json={"taskId": first, "seconds": 0})
    assert foreign.status_code == 404
    assert stranger.status_code == 404
    assert zero.status_code == 422

    finished = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/finish", headers=bearer(token)
    )
    assert finished.status_code == 200
    late = await client.post(url, headers=bearer(token), json={"taskId": first, "seconds": 1})
    assert late.status_code == 409
