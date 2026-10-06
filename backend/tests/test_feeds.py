from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import hash_password
from app.models import Grade
from app.seed.fixtures import SeedData, load_seed_data
from app.seed.generate import DEMO_CANDIDATE_EMAIL, DEMO_EMPLOYER_EMAIL
from app.seed.loader import seed_database, seed_id
from app.services.matching import neighbour_grades, related_specializations
from tests.conftest import API, PASSWORD, bearer, login, register_and_login


@pytest.fixture
async def data(sessionmaker: async_sessionmaker[AsyncSession]) -> SeedData:
    """The demo dataset in the test database; demo accounts use the test password."""
    data = load_seed_data()
    async with sessionmaker() as session:
        await seed_database(session, data, password_hash=hash_password(PASSWORD))
        await session.commit()
    return data


async def get(client: AsyncClient, path: str, token: str, **params: Any) -> Any:
    response = await client.get(f"{API}{path}", params=params, headers=bearer(token))
    assert response.status_code == 200, response.text
    return response.json()


# --- candidate's vacancy feed --------------------------------------------------------------------


async def test_vacancy_feed_is_personal_ranked_and_paginated(
    client: AsyncClient, data: SeedData
) -> None:
    token = await login(client, DEMO_CANDIDATE_EMAIL)
    first = await get(client, "/vacancies/feed", token, page=1, perPage=5)
    second = await get(client, "/vacancies/feed", token, page=2, perPage=5)
    everything = await get(client, "/vacancies/feed", token, perPage=100)

    assert first["personalized"] is True
    assert first["basis"]["category"]["code"] == "backend:middle"
    assert first["total"] == everything["total"] > 5
    assert first["pages"] == -(-first["total"] // 5)
    ids = [item["vacancy"]["id"] for item in first["items"] + second["items"]]
    assert len(set(ids)) == 10
    assert ids == [item["vacancy"]["id"] for item in everything["items"]][:10]

    scores = [item["matchScore"] for item in everything["items"]]
    assert scores == sorted(scores, reverse=True)
    relevant = {"backend"} | related_specializations("backend")
    grades = {Grade.MIDDLE, *neighbour_grades(Grade.MIDDLE)}
    for item in everything["items"]:
        assert item["vacancy"]["category"]["specialization"] in relevant
        assert item["vacancy"]["category"]["grade"] in grades
        assert item["vacancy"]["publishedAt"] is not None
        assert item["reasons"]


async def test_vacancy_feed_filters(client: AsyncClient, data: SeedData) -> None:
    token = await login(client, DEMO_CANDIDATE_EMAIL)
    remote = await get(client, "/vacancies/feed", token, workFormat="remote", perPage=100)
    rich = await get(client, "/vacancies/feed", token, salaryMin=350_000, perPage=100)

    assert remote["items"]
    assert {item["vacancy"]["workFormat"] for item in remote["items"]} == {"remote"}
    assert all(item["vacancy"]["salary"]["to"] >= 350_000 for item in rich["items"])


async def test_reactions_shape_the_feed_views(client: AsyncClient, data: SeedData) -> None:
    token = await login(client, DEMO_CANDIDATE_EMAIL)
    feed = await get(client, "/vacancies/feed", token, perPage=100)
    liked, skipped = (item["vacancy"]["id"] for item in feed["items"][:2])

    for vacancy_id, kind in ((liked, "like"), (skipped, "skip")):
        response = await client.put(
            f"{API}/vacancies/{vacancy_id}/reaction", json={"kind": kind}, headers=bearer(token)
        )
        assert response.status_code == 200, response.text
        assert response.json()["kind"] == kind

    all_view = await get(client, "/vacancies/feed", token, perPage=100)
    unseen = await get(client, "/vacancies/feed", token, view="unseen", perPage=100)
    favourites = await get(client, "/vacancies/feed", token, view="liked")

    all_ids = {item["vacancy"]["id"] for item in all_view["items"]}
    assert liked in all_ids
    assert skipped not in all_ids
    assert {liked, skipped}.isdisjoint(item["vacancy"]["id"] for item in unseen["items"])
    assert [item["vacancy"]["id"] for item in favourites["items"]] == [liked]
    assert favourites["items"][0]["reaction"] == "like"

    undo = await client.delete(f"{API}/vacancies/{skipped}/reaction", headers=bearer(token))
    assert undo.status_code == 204
    restored = await get(client, "/vacancies/feed", token, perPage=100)
    assert skipped in {item["vacancy"]["id"] for item in restored["items"]}


async def test_feed_without_profile_shows_newest_vacancies(
    client: AsyncClient, data: SeedData
) -> None:
    token = await register_and_login(client, "new@fsp.ru")
    feed = await get(client, "/vacancies/feed", token, perPage=100)

    assert (feed["personalized"], feed["basis"]) == (False, None)
    assert feed["total"] == sum(1 for v in data.vacancies if v.published_days_ago is not None)
    dates = [item["vacancy"]["publishedAt"] for item in feed["items"]]
    assert dates == sorted(dates, reverse=True)
    assert all(item["matchScore"] is None for item in feed["items"])


async def test_feeds_are_role_specific(client: AsyncClient, data: SeedData) -> None:
    candidate = await login(client, DEMO_CANDIDATE_EMAIL)
    employer = await login(client, DEMO_EMPLOYER_EMAIL)

    as_employer = await client.get(f"{API}/vacancies/feed", headers=bearer(employer))
    as_candidate = await client.get(f"{API}/candidates", headers=bearer(candidate))

    assert as_employer.status_code == as_candidate.status_code == 403


# --- public vacancies ----------------------------------------------------------------------------


async def test_public_vacancies_hide_drafts(client: AsyncClient, data: SeedData) -> None:
    draft = next(v for v in data.vacancies if v.published_days_ago is None)
    draft_id = seed_id("vacancy", draft.key)

    listing = (await client.get(f"{API}/vacancies", params={"perPage": 100})).json()
    anonymous = await client.get(f"{API}/vacancies/{draft_id}")

    assert listing["total"] == sum(1 for v in data.vacancies if v.published_days_ago is not None)
    assert str(draft_id) not in {item["id"] for item in listing["items"]}
    assert anonymous.status_code == 404


async def test_employer_sees_own_vacancies_with_drafts(client: AsyncClient, data: SeedData) -> None:
    token = await login(client, DEMO_EMPLOYER_EMAIL)
    mine = await get(client, "/vacancies/mine", token, perPage=100)
    company = await client.get(f"{API}/companies/{seed_id('company', 'payflow')}")

    assert mine["total"] == sum(1 for v in data.vacancies if v.company_key == "payflow")
    assert {item["company"]["name"] for item in mine["items"]} == {"ПэйФлоу"}
    assert company.status_code == 200
    assert company.json()["city"] == "Москва"


# --- recruiter's candidate search ----------------------------------------------------------------


async def test_search_hides_private_data_and_ranks_by_strength(
    client: AsyncClient, data: SeedData
) -> None:
    token = await login(client, DEMO_EMPLOYER_EMAIL)
    page = await get(client, "/candidates", token, perPage=100)

    visible = [c for c in data.candidates if c.is_visible_to_employers]
    assert page["engine"] == "database"
    assert page["total"] == len(visible)
    hidden = {str(seed_id("candidate", c.key)) for c in data.candidates if c not in visible}
    assert hidden.isdisjoint(item["candidate"]["id"] for item in page["items"])
    assert all(item["candidate"]["contacts"] is None for item in page["items"])
    strengths = [item["profileStrength"] for item in page["items"]]
    assert strengths == sorted(strengths, reverse=True)
    assert all(item["matchScore"] is None for item in page["items"])


async def test_search_filters(client: AsyncClient, data: SeedData) -> None:
    token = await login(client, DEMO_EMPLOYER_EMAIL)
    category = await get(
        client, "/candidates", token, specialization="backend", grade=["middle", "senior"]
    )
    stack = await get(client, "/candidates", token, stack=["python", "PostgreSQL"], perPage=100)
    fsp = await get(client, "/candidates", token, hasFspAchievements="true", perPage=100)
    verified = await get(client, "/candidates", token, verifiedOnly="true", perPage=100)
    remote = await get(client, "/candidates", token, workFormat="remote", perPage=100)

    assert category["total"] > 0
    for item in category["items"]:
        assert item["candidate"]["category"]["specialization"] == "backend"
        assert item["candidate"]["category"]["grade"] in {"middle", "senior"}
    for item in stack["items"]:
        owned = {tech.lower() for tech in item["candidate"]["stack"]}
        assert {"python", "postgresql"} <= owned
    assert fsp["items"]
    assert all(item["candidate"]["fspAchievements"] for item in fsp["items"])
    assert all(item["candidate"]["gradeVerified"] for item in verified["items"])
    assert all("remote" in item["candidate"]["workFormats"] for item in remote["items"])


async def test_text_search_understands_slang(client: AsyncClient, data: SeedData) -> None:
    token = await login(client, DEMO_EMPLOYER_EMAIL)
    found = await get(client, "/candidates", token, q="питон", perPage=100)

    assert found["total"] > 0
    for item in found["items"]:
        candidate = item["candidate"]
        text = " ".join(
            [candidate["headline"] or "", candidate["about"] or "", *candidate["stack"]]
        )
        assert "python" in text.lower()


async def test_hiring_for_a_vacancy_ranks_by_fit(client: AsyncClient, data: SeedData) -> None:
    token = await login(client, DEMO_EMPLOYER_EMAIL)
    own = seed_id("vacancy", "payflow-02")  # Go-разработчик в команду антифрода
    foreign = seed_id("vacancy", "korzinka-01")

    ranked = await get(client, "/candidates", token, vacancyId=str(own), perPage=20)
    rejected = await client.get(
        f"{API}/candidates", params={"vacancyId": str(foreign)}, headers=bearer(token)
    )

    scores = [item["matchScore"] for item in ranked["items"]]
    assert scores == sorted(scores, reverse=True)
    assert ranked["items"][0]["candidate"]["category"]["specialization"] == "backend"
    assert any(reason.startswith("Стек вакансии") for reason in ranked["items"][0]["reasons"])
    assert rejected.status_code == 404


async def test_recruiter_favourites(client: AsyncClient, data: SeedData) -> None:
    token = await login(client, DEMO_EMPLOYER_EMAIL)
    first, second = (await get(client, "/candidates", token, perPage=2))["items"]
    liked, skipped = first["candidate"]["id"], second["candidate"]["id"]

    for candidate_id, kind in ((liked, "like"), (skipped, "skip")):
        response = await client.put(
            f"{API}/candidates/{candidate_id}/reaction", json={"kind": kind}, headers=bearer(token)
        )
        assert response.status_code == 200, response.text

    all_view = await get(client, "/candidates", token, perPage=100)
    favourites = await get(client, "/candidates", token, view="liked")

    assert skipped not in {item["candidate"]["id"] for item in all_view["items"]}
    assert [item["candidate"]["id"] for item in favourites["items"]] == [liked]


# --- single profile ------------------------------------------------------------------------------


async def test_profile_visibility_and_contacts(client: AsyncClient, data: SeedData) -> None:
    employer = await login(client, DEMO_EMPLOYER_EMAIL)
    candidate = await login(client, DEMO_CANDIDATE_EMAIL)
    demo_id = seed_id("candidate", data.candidates[0].key)
    other = next(c for c in data.candidates[1:] if c.is_visible_to_employers)
    hidden = next(c for c in data.candidates if not c.is_visible_to_employers)

    seen_by_employer = await get(client, f"/candidates/{demo_id}", employer)
    own = await get(client, f"/candidates/{demo_id}", candidate)
    foreign = await client.get(
        f"{API}/candidates/{seed_id('candidate', other.key)}", headers=bearer(candidate)
    )
    private = await client.get(
        f"{API}/candidates/{seed_id('candidate', hidden.key)}", headers=bearer(employer)
    )

    assert seen_by_employer["contacts"] is None
    assert own["contacts"]["email"] == DEMO_CANDIDATE_EMAIL
    assert foreign.status_code == private.status_code == 404
