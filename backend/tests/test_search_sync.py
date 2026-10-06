from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, timedelta

from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import CandidateProfile
from app.repositories.candidate import CandidateRepository
from app.search.elastic import ElasticSearchState
from app.seed.fixtures import load_seed_data
from app.seed.loader import seed_database, seed_id


class FakeIndex:
    """Collects upserts instead of talking to Elasticsearch."""

    alias = "fake"

    def __init__(self) -> None:
        self.upserted: list[CandidateProfile] = []

    async def upsert(self, profiles: Iterable[CandidateProfile]) -> int:
        batch = list(profiles)
        self.upserted += batch
        return len(batch)


def state_with_fake_index() -> tuple[ElasticSearchState, FakeIndex]:
    # The client is never used: nothing connects until a request is sent.
    state = ElasticSearchState(AsyncElasticsearch("http://localhost:1"), "fake")
    fake = FakeIndex()
    state.index = fake  # type: ignore[assignment]
    return state, fake


async def test_sync_pushes_changed_profiles_and_is_throttled() -> None:
    state, fake = state_with_fake_index()
    asked: list[datetime] = []
    profile = CandidateProfile(display_name="Кандидат")

    async def changed(since: datetime) -> Sequence[CandidateProfile]:
        asked.append(since)
        return [profile]

    first = await state.sync(changed)
    throttled = await state.sync(changed)
    state.SYNC_SECONDS = 0
    second = await state.sync(changed)

    assert (first, throttled, second) == (1, 0, 1)
    assert fake.upserted == [profile, profile]
    # After a restart the index catches up on a day; then only since the previous sync.
    assert datetime.now(UTC) - asked[0] > timedelta(hours=23)
    assert datetime.now(UTC) - asked[1] < timedelta(minutes=1)


async def test_updated_since_finds_profiles_changed_by_other_features(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    data = load_seed_data()
    async with sessionmaker() as session:
        await seed_database(session, data, password_hash="not-a-real-hash")
        await session.commit()
    before = datetime.now(UTC) - timedelta(minutes=5)

    async with sessionmaker() as session:
        candidates = CandidateRepository(session)
        assert await candidates.updated_since(before) == []  # demo rows are dated in the past

        # What the testing service does when a test is passed.
        profile = await candidates.get(seed_id("candidate", data.candidates[1].key))
        assert profile is not None
        profile.assessment_score = 95.0
        await session.commit()

    async with sessionmaker() as session:
        changed = await CandidateRepository(session).updated_since(before)
        assert [item.id for item in changed] == [seed_id("candidate", data.candidates[1].key)]
