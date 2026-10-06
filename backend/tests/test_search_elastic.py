"""Elasticsearch must return exactly what the database engine returns (same filters, same order).

Runs against a real cluster only: `TEST_ELASTICSEARCH_URL=http://localhost:9200 uv run pytest`.
"""

import os
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Grade, WorkFormat
from app.repositories.candidate import CandidateRepository
from app.repositories.vacancy import VacancyRepository
from app.search.base import CandidateSearchQuery
from app.search.database import DatabaseCandidateSearch
from app.search.elastic import CandidateIndex, ElasticCandidateSearch, ElasticSearchState
from app.seed.fixtures import load_seed_data
from app.seed.loader import seed_database, seed_id
from app.services.matching import VacancyFacts

ES_URL = os.environ.get("TEST_ELASTICSEARCH_URL", "")

pytestmark = pytest.mark.skipif(not ES_URL, reason="TEST_ELASTICSEARCH_URL is not set")

QUERIES = (
    CandidateSearchQuery(),
    CandidateSearchQuery(specialization="backend", grades=(Grade.MIDDLE, Grade.SENIOR)),
    CandidateSearchQuery(stack=("python", "PostgreSQL"), has_fsp=True),
    CandidateSearchQuery(has_fsp=False, verified_only=True),
    CandidateSearchQuery(city="москва", work_formats=(WorkFormat.REMOTE,)),
    CandidateSearchQuery(salary_max=250_000, experience_min=3),
    CandidateSearchQuery(sort="assessment"),
    CandidateSearchQuery(sort="salary"),
    CandidateSearchQuery(sort="experience", specialization="qa"),
)


@dataclass
class Engines:
    elastic: ElasticCandidateSearch
    database: DatabaseCandidateSearch
    vacancies: list[VacancyFacts]


@pytest.fixture
async def engines(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncIterator[Engines]:
    async with sessionmaker() as session:
        await seed_database(session, load_seed_data(), password_hash="not-a-real-hash")
        await session.commit()

    client = AsyncElasticsearch(ES_URL)
    index = CandidateIndex(client, f"kadry-test-{uuid.uuid4().hex[:8]}")
    try:
        async with sessionmaker() as session:
            candidates = CandidateRepository(session)
            await index.rebuild(await candidates.all())
            rows = await VacancyRepository(session).published()
            yield Engines(
                ElasticCandidateSearch(index),
                DatabaseCandidateSearch(candidates),
                [VacancyFacts.of(vacancy) for vacancy, _ in rows],
            )
    finally:
        await client.indices.delete(index=f"{index.alias}-*")
        await client.close()


async def test_filters_and_orders_match_the_database(engines: Engines) -> None:
    for query in QUERIES:
        elastic = await engines.elastic.search(query, offset=0, limit=500)
        database = await engines.database.search(query, offset=0, limit=500)
        assert elastic.total == database.total, query
        assert elastic.ids == database.ids, query


async def test_fit_to_every_vacancy_matches_python(engines: Engines) -> None:
    for vacancy in engines.vacancies:
        query = CandidateSearchQuery(vacancy=vacancy)
        elastic = await engines.elastic.search(query, offset=0, limit=500)
        database = await engines.database.search(query, offset=0, limit=500)
        assert elastic.ids == database.ids, vacancy


async def test_pages_are_slices_of_one_order(engines: Engines) -> None:
    query = CandidateSearchQuery(vacancy=engines.vacancies[0])
    whole = await engines.elastic.search(query, offset=0, limit=500)
    second = await engines.elastic.search(query, offset=10, limit=10)
    assert second.ids == whole.ids[10:20]
    assert second.total == whole.total


async def test_text_search_handles_slang_and_morphology(engines: Engines) -> None:
    slang = await engines.elastic.search(CandidateSearchQuery(text="питон"), offset=0, limit=50)
    morphology = await engines.elastic.search(
        CandidateSearchQuery(text="разработчиками"), offset=0, limit=50
    )
    typo = await engines.elastic.search(CandidateSearchQuery(text="kuberentes"), offset=0, limit=50)
    assert slang.total > 0
    assert morphology.total > 0
    assert typo.total > 0


async def test_sync_brings_new_test_results_into_search(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    data = load_seed_data()
    async with sessionmaker() as session:
        await seed_database(session, data, password_hash="not-a-real-hash")
        await session.commit()
    untested = next(
        c for c in data.candidates if c.assessment_score is None and c.is_visible_to_employers
    )
    candidate_id = seed_id("candidate", untested.key)
    verified = CandidateSearchQuery(verified_only=True)

    client = AsyncElasticsearch(ES_URL)
    state = ElasticSearchState(client, f"kadry-test-{uuid.uuid4().hex[:8]}")
    search = ElasticCandidateSearch(state.index)
    try:
        async with sessionmaker() as session:
            assert await state.ready(CandidateRepository(session).all)
            before = await search.search(verified, offset=0, limit=500)

            # What the testing service does when the candidate passes the test.
            profile = await CandidateRepository(session).get(candidate_id)
            assert profile is not None
            profile.assessment_score = 88.0
            await session.commit()

            state.SYNC_SECONDS = 0
            assert await state.sync(CandidateRepository(session).updated_since) >= 1
            after = await search.search(verified, offset=0, limit=500)
    finally:
        await client.indices.delete(index=f"{state.index.alias}-*")
        await client.close()

    assert candidate_id not in before.ids
    assert candidate_id in after.ids
