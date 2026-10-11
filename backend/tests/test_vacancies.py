"""The employer's own vacancies: a draft, its publication and later edits."""

from typing import Any

from httpx import AsyncClient

from tests.conftest import API, bearer, register_and_login
from tests.test_cabinet import COMPANY

VACANCY: dict[str, Any] = {
    "title": "Backend-разработчик (платежи)",
    "description": (
        "Команда процессинга проводит платежи по картам и СБП. Задачи: сервисы на FastAPI, "
        "интеграции через Kafka, разбор инцидентов. Требования: уверенный Python и PostgreSQL, "
        "опыт код-ревью."
    ),
    "specialization": "backend",
    "grades": ["senior", "middle"],
    "stackRequired": [" Python ", "PostgreSQL", "python"],
    "stackNice": ["Kafka", "postgresql"],
    "salary": {"from": 200_000, "to": 320_000},
    "workFormat": "hybrid",
    "city": "Москва",
    "employmentTypes": ["full"],
    "benefits": ["dms"],
}


async def employer_with_company(client: AsyncClient, email: str, inn: str = COMPANY["inn"]) -> str:
    token = await register_and_login(client, email, role="employer")
    saved = await client.put(
        f"{API}/companies/me", headers=bearer(token), json={**COMPANY, "inn": inn}
    )
    assert saved.status_code == 200, saved.text
    return token


async def test_vacancy_needs_a_company_and_the_employer_role(client: AsyncClient) -> None:
    employer = await register_and_login(client, "hr-new@fsp.ru", role="employer")
    candidate = await register_and_login(client, "dev@fsp.ru")

    no_company = await client.post(f"{API}/vacancies", headers=bearer(employer), json=VACANCY)
    foreign_role = await client.post(f"{API}/vacancies", headers=bearer(candidate), json=VACANCY)

    assert no_company.status_code == 404
    assert foreign_role.status_code == 403


async def test_draft_is_published_and_edited_by_its_company_only(client: AsyncClient) -> None:
    owner = await employer_with_company(client, "hr@fsp.ru")
    stranger = await employer_with_company(client, "hr-other@fsp.ru", inn="500100732259")

    created = await client.post(
        f"{API}/vacancies", headers=bearer(owner), json={**VACANCY, "publish": False}
    )
    assert created.status_code == 201, created.text
    draft = created.json()
    url = f"{API}/vacancies/{draft['id']}"

    # Grades are kept in order, the stack has no repeats, a technology is listed once.
    assert (draft["publishedAt"], draft["grades"]) == (None, ["middle", "senior"])
    assert draft["category"]["grade"] == "middle"
    assert (draft["stackRequired"], draft["stackNice"]) == (["Python", "PostgreSQL"], ["Kafka"])
    assert draft["stack"] == ["Python", "PostgreSQL", "Kafka"]

    public = await client.get(f"{API}/vacancies")
    mine = await client.get(f"{API}/vacancies/mine", headers=bearer(owner))
    assert public.json()["total"] == 0
    assert [item["id"] for item in mine.json()["items"]] == [draft["id"]]
    assert (await client.get(url, headers=bearer(stranger))).status_code == 404

    foreign = await client.patch(url, headers=bearer(stranger), json=VACANCY)
    assert foreign.status_code == 404

    published = await client.patch(url, headers=bearer(owner), json=VACANCY)
    assert published.status_code == 200, published.text
    first_date = published.json()["publishedAt"]
    assert first_date is not None
    assert [item["id"] for item in (await client.get(f"{API}/vacancies")).json()["items"]] == [
        draft["id"]
    ]

    edited = await client.patch(
        url,
        headers=bearer(owner),
        json={**VACANCY, "title": "Senior Backend-разработчик", "workFormat": "remote"},
    )
    body = edited.json()
    # An edit keeps the date of the first publication; a remote vacancy has no office city.
    assert (body["title"], body["city"]) == ("Senior Backend-разработчик", None)
    # SQLite reads the date back without its time zone.
    assert body["publishedAt"].removesuffix("Z") == first_date.removesuffix("Z")

    hidden = await client.patch(url, headers=bearer(owner), json={**VACANCY, "publish": False})
    assert hidden.json()["publishedAt"] is None
    assert (await client.get(f"{API}/vacancies")).json()["total"] == 0


async def test_vacancy_form_rules(client: AsyncClient) -> None:
    token = await employer_with_company(client, "hr-rules@fsp.ru")

    async def status_of(patch: dict[str, Any]) -> int:
        response = await client.post(
            f"{API}/vacancies", headers=bearer(token), json={**VACANCY, **patch}
        )
        return response.status_code

    assert await status_of({"grades": ["junior", "senior"]}) == 422
    assert await status_of({"city": " "}) == 422
    assert await status_of({"description": "Коротко"}) == 422
    assert await status_of({"salary": {"from": 300_000, "to": 200_000}}) == 422
    assert await status_of({"stackRequired": [" "]}) == 422
    # A test left in production: no word in the title, a keyboard mash, a salary of 1–2 ₽.
    assert await status_of({"title": "8II8MI ,"}) == 400
    mash = "m7 8irtrmi87itm8mi,7tm87tm8mi7mti87tmi78tmi78irjgheauo4hrtuierhafu;khrweau" * 3
    assert await status_of({"description": mash}) == 400
    assert await status_of({"salary": {"from": 1, "to": 2}}) == 422
    assert await status_of({"specialization": "astrology"}) == 400
    assert await status_of({"workFormat": "remote", "city": None}) == 201
