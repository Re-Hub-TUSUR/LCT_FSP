"""Candidate search on Elasticsearch: the index lifecycle and queries."""

import asyncio
import logging
import time
import uuid
from collections.abc import Awaitable, Callable, Iterable, Sequence
from datetime import UTC, datetime
from typing import Any

from elasticsearch import ApiError, AsyncElasticsearch, NotFoundError, TransportError
from elasticsearch.helpers import BulkIndexError, async_bulk

from app.core.config import Settings
from app.models import CandidateProfile
from app.schemas.candidate import SearchEngine
from app.search.base import CandidateSearchQuery, SearchHits, SearchUnavailableError
from app.search.documents import MAPPINGS, SETTINGS, candidate_document
from app.search.query import build_search_body

logger = logging.getLogger(__name__)

ElasticErrors = (ApiError, TransportError, BulkIndexError)

ProfilesLoader = Callable[[], Awaitable[Sequence[CandidateProfile]]]


def create_client(settings: Settings) -> AsyncElasticsearch:
    # Short timeouts: a slow cluster falls back to the database instead of hanging.
    return AsyncElasticsearch(settings.elasticsearch_url, request_timeout=5, max_retries=1)


class CandidateIndex:
    """An alias over versioned indices.

    A rebuild fills a fresh index and swaps the alias atomically, so searches never see a half-built
    index and a mapping change needs no downtime.
    """

    def __init__(self, client: AsyncElasticsearch, alias: str) -> None:
        self._client = client
        self.alias = alias

    async def exists(self) -> bool:
        return bool(await self._client.indices.exists_alias(name=self.alias))

    async def rebuild(self, profiles: Iterable[CandidateProfile]) -> int:
        name = f"{self.alias}-{datetime.now(UTC):%Y%m%d%H%M%S%f}"
        await self._client.indices.create(index=name, settings=SETTINGS, mappings=MAPPINGS)
        actions = (
            {"_index": name, "_id": str(profile.id), "_source": candidate_document(profile)}
            for profile in profiles
        )
        indexed, _ = await async_bulk(self._client, actions, refresh="wait_for")
        swap: list[dict[str, Any]] = [{"add": {"index": name, "alias": self.alias}}]
        swap += [{"remove_index": {"index": old}} for old in await self._indices()]
        await self._client.indices.update_aliases(actions=swap)
        return indexed

    async def upsert(self, profile: CandidateProfile) -> None:
        """Keeps one profile in sync after it changes (profile editing, test results)."""
        await self._client.index(
            index=self.alias,
            id=str(profile.id),
            document=candidate_document(profile),
            refresh="wait_for",
        )

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
    """Owns the client and prepares the index lazily.

    The API starts even when Elasticsearch is still booting or down: until the index is ready the
    search runs on the database, and a new attempt is made at most every `RETRY_SECONDS`.
    """

    RETRY_SECONDS = 30.0

    def __init__(self, client: AsyncElasticsearch, alias: str) -> None:
        self.client = client
        self.index = CandidateIndex(client, alias)
        self._ready = False
        self._failed_at: float | None = None
        self._lock = asyncio.Lock()

    async def ready(self, load_profiles: ProfilesLoader) -> bool:
        if self._ready:
            return True
        if self._failed_at is not None and time.monotonic() - self._failed_at < self.RETRY_SECONDS:
            return False
        async with self._lock:
            if self._ready:
                return True
            try:
                if not await self.index.exists():
                    indexed = await self.index.rebuild(await load_profiles())
                    logger.info("Search index %s built: %d candidates", self.index.alias, indexed)
                self._ready = True
                self._failed_at = None
            except ElasticErrors as exc:
                self.mark_unavailable()
                logger.warning("Elasticsearch unavailable, searching the database: %s", exc)
        return self._ready

    def mark_unavailable(self) -> None:
        self._ready = False
        self._failed_at = time.monotonic()

    async def close(self) -> None:
        await self.client.close()
