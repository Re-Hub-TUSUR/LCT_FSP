"""Regressions for the browser run of October 2026 and the vacancy list that fell on a deploy."""

import uuid
from collections.abc import AsyncIterator

from httpx import ASGITransport, AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.types import Message, Receive, Scope, Send

from app.dependencies.common import get_db_session
from app.main import create_app
from app.models import Company, Vacancy
from app.repositories.conversation import ConversationRepository
from app.services.cities import install_reference_cities
from tests.conftest import API, bearer, register_and_login
from tests.test_cabinet import COMPANY, RESUME, employer_with_company
from tests.test_vacancies import VACANCY


async def test_a_salary_saved_before_the_limit_does_not_break_the_list(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    owner = await employer_with_company(client, "old-salary@fsp.ru")
    created = await client.post(f"{API}/vacancies", headers=bearer(owner), json=VACANCY)
    assert created.status_code == 201, created.text
    async with sessionmaker() as session:
        await session.execute(
            update(Vacancy)
            .where(Vacancy.id == uuid.UUID(created.json()["id"]))
            .values(salary_to=1_234_552_097)
        )
        await session.commit()

    # The public table is open to a guest: one old row must not answer 500 for all of them.
    listed = await client.get(f"{API}/vacancies")
    assert listed.status_code == 200, listed.text
    assert listed.json()["items"][0]["salary"]["to"] == 1_234_552_097

    # The limit still holds for what comes in.
    too_much = {**VACANCY, "salary": {"from": 200_000, "to": 1_234_552_097}}
    refused = await client.post(f"{API}/vacancies", headers=bearer(owner), json=too_much)
    assert refused.status_code == 422


async def test_contacts_are_something_an_employer_can_use(client: AsyncClient) -> None:
    token = await register_and_login(client, "contacts@fsp.ru")
    for wrong in ({"phone": "12"}, {"phone": "позвоните мне"}, {"telegram": "!!"}):
        refused = await client.patch(
            f"{API}/candidates/me", headers=bearer(token), json={**RESUME, **wrong}
        )
        assert refused.status_code == 422, wrong

    saved = await client.patch(
        f"{API}/candidates/me",
        headers=bearer(token),
        json={**RESUME, "phone": "+7 (900) 123-45-67", "telegram": "https://t.me/ivan_dev"},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["contacts"]["phone"] == "+7 (900) 123-45-67"
    assert saved.json()["contacts"]["telegram"] == "ivan_dev"


async def test_the_unit_of_work_is_committed_before_the_answer_is_sent(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    """Committed after the answer, a save loses to the request that follows it: the chat list
    reloaded right after «Ответить» came back empty."""
    events: list[str] = []
    async with sessionmaker() as session:
        await install_reference_cities(session)
        await session.commit()

    async def traced_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            events.append("open")
            try:
                yield session
                await session.commit()
                events.append("commit")
            except Exception:
                await session.rollback()
                events.append("rollback")
                raise

    app = create_app()
    app.dependency_overrides[get_db_session] = traced_session

    async def traced_app(scope: Scope, receive: Receive, send: Send) -> None:
        async def traced_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                events.append(f"answer {message['status']}")
            await send(message)

        await app(scope, receive, traced_send)

    transport = ASGITransport(app=traced_app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        token = await register_and_login(http, "order@fsp.ru")
        events.clear()
        # Auth, the service and its repositories share one session, committed before the answer.
        saved = await http.patch(f"{API}/candidates/me", headers=bearer(token), json=RESUME)
        assert saved.status_code == 200, saved.text
        assert events == ["open", "commit", "answer 200"]

        events.clear()
        refused = await http.put(f"{API}/companies/me", headers=bearer(token), json=COMPANY)
        assert refused.status_code == 403
        assert events == ["open", "rollback", "answer 403"]


async def test_a_pair_has_one_conversation(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    candidate = await register_and_login(client, "pair@fsp.ru")
    profile = await client.patch(f"{API}/candidates/me", headers=bearer(candidate), json=RESUME)
    await employer_with_company(client, "pair-hr@fsp.ru")
    async with sessionmaker() as session:
        company_id = await session.scalar(Company.__table__.select().with_only_columns(Company.id))
        assert company_id is not None
        chats = ConversationRepository(session)
        pair = {"company_id": company_id, "candidate_id": uuid.UUID(profile.json()["id"])}
        first = await chats.get_or_create(**pair)
        second = await chats.get_or_create(**pair)
        assert first.id == second.id
