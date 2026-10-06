"""`uv run python -m app.seed [--force]`: load the demo dataset into the configured database."""

import argparse
import asyncio
import os
import sys

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import get_engine, get_sessionmaker
from app.search.elastic import ElasticErrors
from app.search.reindex import rebuild_search_index
from app.seed.fixtures import load_seed_data
from app.seed.loader import (
    DEFAULT_PASSWORD,
    PASSWORD_ENV,
    SeedConflictError,
    SeedSummary,
    seed_database,
)


async def _seed(password: str) -> SeedSummary:
    data = load_seed_data()
    try:
        async with get_sessionmaker()() as session:
            summary = await seed_database(session, data, password_hash=hash_password(password))
            await session.commit()
        await _reindex()
    finally:
        await get_engine().dispose()
    return summary


async def _reindex() -> None:
    """Demo profiles get new rows, so the search index is rebuilt right away."""
    try:
        indexed = await rebuild_search_index(get_settings())
    except ElasticErrors as exc:
        print(
            f"Search index not rebuilt ({exc}); run `python -m app.search` later.",
            file=sys.stderr,
        )
        return
    if indexed is not None:
        print(f"Search index rebuilt: {indexed} candidates.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.seed",
        description="Load demo companies, vacancies and candidates (replaces earlier demo rows).",
    )
    parser.add_argument(
        "--force", action="store_true", help="allow loading demo data with APP_ENV=production"
    )
    args = parser.parse_args(argv)

    if get_settings().is_production and not args.force:
        print("APP_ENV=production: demo data is loaded only with --force", file=sys.stderr)
        return 1

    try:
        summary = asyncio.run(_seed(os.environ.get(PASSWORD_ENV) or DEFAULT_PASSWORD))
    except SeedConflictError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(
        f"Demo data loaded: {summary.companies} companies, {summary.vacancies} vacancies, "
        f"{summary.candidates} candidates, {summary.fsp_achievements} FSP results."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
