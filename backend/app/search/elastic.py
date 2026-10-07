"""Candidate search on Elasticsearch: the index lifecycle and queries."""

import asyncio
import logging
import time
import uuid
from collections.abc import Awaitable, Callable, Iterable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from elasticsearch import ApiError, AsyncElasticsearch, NotFoundError, TransportError
from elasticsearch.helpers import BulkIndexError, async_bulk

from app.core.config import Settings
from app.models import CandidateProfile
from app.schemas.candidate import SearchEngine
from app.search.base import CandidateSearchQuery, SearchHits, SearchUnavailableError
from app.search.documents import INDEX_VERSION, MAPPINGS, SETTINGS, candidate_document
from app.search.query import build_search_body

logger = logging.getLogger(__name__)

ElasticErrors = (ApiError, TransportError, BulkIndexError)

ProfilesLoader = Callable[[], Awaitable[Sequence[CandidateProfile]]]
ChangedProfilesLoader = Callable[[datetime], Awaitable[Sequence[CandidateProfile]]]


def create_client(settings: Settings) -> AsyncElasticsearch:
    # Short timeouts: a slow cluster makes the API fall back to the database, not hang.
    return AsyncElasticsearch(settings.elasticsearch_url, request_timeout=5, max_retries=1)


class CandidateIndex:
    """An alias over versioned indices.

    A rebuild fills a fresh index and swaps the alias atomically, so searches never see a half-built
    index and a mapping change needs no downtime.
    """

    def __init__(self, client: AsyncElasticsearch, alias: str) -> None:
        self._client = client
        self.alias = alias

    async def is_current(self) -> bool:
        """The alias exists and points at an index built from today's `INDEX_VERSION`."""
        try:
            response = await self._client.indices.get_mapping(index=self.alias)
        except NotFoundError:
            return False
        versions = {
            index.get("mappings", {}).get("_meta", {}).get("version")
            for index in response.body.values()
        }
        return versions == {INDEX_VERSION}

    async def rebuild(self, profiles: Iterable[CandidateProfile]) -> int:
        name = f"{self.alias}-{datetime.now(UTC):%Y%m%d%H%M%S%f}"
        mappings = {**MAPPINGS, "_meta": {"version": INDEX_VERSION}}
        await self._client.indices.create(index=name, settings=SETTINGS, mappings=mappings)
        actions = (
            {"_index": name, "_id": str(profile.id), "_source": candidate_document(profile)}
            for profile in profiles
        )
        indexed, _ = await async_bulk(self._client, actions, refresh="wait_for")
        swap: list[dict[str, Any]] = [{"add": {"index": name, "alias": self.alias}}]
        swap += [{"remove_index": {"index": old}} for old in await self._indices()]
        await self._client.indices.update_aliases(actions=swap)
        return indexed

    async def upsert(self, profiles: Iterable[CandidateProfile]) -> int:
        """Overwrites the documents of changed profiles; visible to the next search at once."""
        actions = (
            {"_index": self.alias, "_id": str(profile.id), "_source": candidate_document(profile)}
            for profile in profiles
        )
        indexed, _ = await async_bulk(self._client, actions, refresh=True)
        return indexed

    async def search(self, body: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.search(index=self.alias, body=body)
        return dict(response.body)

    async def _indices(self) -> list[str]:
        try:
            response = await self._client.indices.get_alias(name=self.alias)
        except NotFoundError:
            return []
        return list(response.body)


class ElasticCandidateSearch:
    name: SearchEngine = "elasticsearch"

    def __init__(self, index: CandidateIndex) -> None:
        self._index = index

    async def search(self, query: CandidateSearchQuery, *, offset: int, limit: int) -> SearchHits:
        body = build_search_body(query, offset=offset, limit=limit)
        try:
            response = await self._index.search(body)
        except ElasticErrors as exc:
            raise SearchUnavailableError(str(exc)) from exc
        hits = response["hits"]
        return SearchHits(
            ids=[uuid.UUID(hit["_id"]) for hit in hits["hits"]],
            total=int(hits["total"]["value"]),
        )


class ElasticSearchState:
    """Owns the client, prepares the index lazily and keeps it in step with the database.

    The API starts even when Elasticsearch is still booting or down: until the index is ready the
    search runs on the database, and a new attempt is made at most every `RETRY_SECONDS`.

    Profiles change outside the search code (test results, profile editing), so before a search
    the index takes the profiles updated since the previous sync (`updated_at`), at most every
    `SYNC_SECONDS`. A full rebuild (`python -m app.search`) is only needed after bulk loads.
    """

    RETRY_SECONDS = 30.0
    SYNC_SECONDS = 2.0
    # Covers clock skew between the API and the database and transactions committed late.
    SYNC_OVERLAP = timedelta(seconds=10)
    # After a restart the time of the last sync is unknown: catch up on the last day.
    FIRST_SYNC_LOOKBACK = timedelta(days=1)

    def __init__(self, client: AsyncElasticsearch, alias: str) -> None:
        self.client = client
        self.index = CandidateIndex(client, alias)
        self._ready = False
        self._failed_at: float | None = None
        self._lock = asyncio.Lock()
        self._synced_at: datetime | None = None
        self._sync_checked: float | None = None

    async def ready(self, load_profiles: ProfilesLoader) -> bool:
        if self._ready:
            return True
        if self._failed_at is not None and time.monotonic() - self._failed_at < self.RETRY_SECONDS:
            return False
        async with self._lock:
            if self._ready:
                return True
            try:
                # Missing, or built from another index definition: build a fresh one.
                if not await self.index.is_current():
                    started = datetime.now(UTC)
                    indexed = await self.index.rebuild(await load_profiles())
                    self._synced_at = started
                    logger.info("Search index %s built: %d candidates", self.index.alias, indexed)
                self._ready = True
                self._failed_at = None
            except ElasticErrors as exc:
                self.mark_unavailable()
                logger.warning("Elasticsearch unavailable, searching the database: %s", exc)
        return self._ready

    async def sync(self, load_changed: ChangedProfilesLoader) -> int:
        """Pushes profiles changed since the last sync into the index; returns how many."""
        now = time.monotonic()
        if self._sync_checked is not None and now - self._sync_checked < self.SYNC_SECONDS:
            return 0
        started = datetime.now(UTC)
        since = (self._synced_at or started - self.FIRST_SYNC_LOOKBACK) - self.SYNC_OVERLAP
        changed = await load_changed(since)
        indexed = await self.index.upsert(changed) if changed else 0
        self._synced_at = started
        self._sync_checked = now
        return indexed

    def mark_unavailable(self) -> None:
        self._ready = False
        self._failed_at = time.monotonic()

    async def close(self) -> None:
        await self.client.close()
