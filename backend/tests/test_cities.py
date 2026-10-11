"""City dictionary: suggestions, a refused free-text city, and a filter by place id."""

from typing import Any

from httpx import AsyncClient

from app.models.enums import JobStatus, WorkFormat
from app.search.base import CandidateSearchQuery
from app.search.filters import FilterFacts, passes
from app.search.query import build_search_body
from app.seed.cities import russian_label
from tests.conftest import API, bearer, register_and_login
from tests.test_cabinet import RESUME
from tests.test_vacancies import VACANCY, employer_with_company


def _facts(*, city_id: int, city: str = "москва") -> FilterFacts:
    return FilterFacts(
        specialization="backend",
        grade=None,
        verified=False,
        fsp_marks=frozenset(),
        experience=3,
        stack=frozenset(),
        salary=None,
        formats=frozenset({WorkFormat.OFFICE.value}),
        city=city,
        relocation=False,
        employment=frozenset(),
        status=JobStatus.OPEN.value,
        last_active=None,
        city_id=city_id,
    )


def test_the_russian_name_is_the_one_the_form_shows() -> None:
    assert (
        russian_label(
            "Moscow",
            ["Maskav", "Moskva", "Moskova", "Musko", "Москва", "Москова", "Москъва", "Муско"],
        )
        == "Москва"
    )
    assert (
        russian_label(
            "Saint Petersburg",
            ["Piter", "Питер", "СПб", "Санкт Петербург", "Санкт-Петербург", "Ленинград"],
        )
        == "Санкт-Петербург"
    )
    assert russian_label("Kazan", ["Kuzon", "Кузон", "Къазан", "Казан", "Казань"]) == "Казань"
    assert russian_label("Nizhniy Novgorod", ["Горький", "Нижний Новгород"]) == "Нижний Новгород"
    assert russian_label("Kaliningrad", ["Калининград"]) == "Калининград"
    assert (
        russian_label("Togliatti-on-the-Volga", ["Toliati", "Tolyatti", "Толиати", "Тольятти"])
        == "Тольятти"
    )
    assert russian_label("Ulyanovsk", ["Ulyanovsk", "Уляновск", "Ульяновск"]) == "Ульяновск"


async def test_search_finds_prefix_alias_and_a_full_name(client: AsyncClient) -> None:
    moscow = await client.get(f"{API}/cities/search", params={"q": "Моск"})
    assert moscow.status_code == 200, moscow.text
    assert moscow.json()[0]["name"] == "Москва"
    assert moscow.json()[0]["id"] == 524901

    peter = await client.get(f"{API}/cities/search", params={"q": "СПб"})
    assert peter.json()[0]["id"] == 498817
    assert peter.json()[0]["name"] == "Санкт-Петербург"

    nizhny = await client.get(f"{API}/cities/search", params={"q": "Нижний Новгород"})
    assert nizhny.json()[0]["id"] == 520555

    prefixed = await client.get(f"{API}/cities/search", params={"q": "г. Москва"})
    assert prefixed.json()[0]["id"] == 524901
    short = await client.get(f"{API}/cities/search", params={"q": "гор. Казань"})
    assert short.json()[0]["id"] == 551487


async def test_a_city_must_be_chosen_from_the_list(client: AsyncClient) -> None:
    token = await employer_with_company(client, "hr-city@fsp.ru", inn="500100732259")

    invented = await client.post(
        f"{API}/vacancies",
        headers=bearer(token),
        json={**VACANCY, "city": "Атлантида"},
    )
    assert invented.status_code == 400, invented.text
    assert "списка" in invented.json()["error"]["message"]

    unknown_id = await client.post(
        f"{API}/vacancies",
        headers=bearer(token),
        json={**VACANCY, "cityId": 1, "city": None},
    )
    assert unknown_id.status_code == 400

    chosen = await client.post(
        f"{API}/vacancies",
        headers=bearer(token),
        json={**VACANCY, "cityId": 524901, "city": None},
    )
    assert chosen.status_code == 201, chosen.text
    body = chosen.json()
    assert (body["cityId"], body["city"], body["cityRegion"]) == (524901, "Москва", "Москва")

    access = await register_and_login(client, "city-dev@fsp.ru")
    refused = await client.patch(
        f"{API}/candidates/me",
        headers=bearer(access),
        json={**RESUME, "city": "Атлантида"},
    )
    assert refused.status_code == 400
    assert "списка" in refused.json()["error"]["message"]


def test_elasticsearch_filters_by_city_id() -> None:
    query = CandidateSearchQuery(
        city_ids=(524901,),
        work_formats=(WorkFormat.OFFICE,),
        include_relocation=False,
    )
    body: dict[str, Any] = build_search_body(query, offset=0, limit=10)
    assert {"terms": {"city_id": [524901]}} in _clauses(body)
    assert passes(_facts(city_id=524901), query)
    # Same spelling, another place: the name is not enough.
    assert not passes(_facts(city_id=498817, city="москва"), query)


def _clauses(body: dict[str, Any]) -> list[Any]:
    """Every filter clause of the search body, including ones nested under bool."""
    found: list[Any] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if "terms" in node or "term" in node:
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(body)
    return found
