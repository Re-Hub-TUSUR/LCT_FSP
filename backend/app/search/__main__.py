"""`uv run python -m app.search`: rebuild the candidate search index from the database."""

import asyncio
import sys

from app.core.config import get_settings
from app.db.session import get_engine
from app.search.elastic import ElasticErrors
from app.search.reindex import rebuild_search_index


async def _rebuild() -> int | None:
    try:
        return await rebuild_search_index(get_settings())
    finally:
        await get_engine().dispose()


def main() -> int:
    try:
        indexed = asyncio.run(_rebuild())
    except ElasticErrors as exc:
        print(f"Elasticsearch is unavailable: {exc}", file=sys.stderr)
        return 1
    if indexed is None:
        print("ELASTICSEARCH_URL is empty: the search runs on the database.", file=sys.stderr)
        return 1
    print(f"Search index rebuilt: {indexed} candidates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
