"""`uv run python -m app.seed [--if-missing] [--force]`: load the demo dataset into the database.

Without flags the demo rows are replaced. `--if-missing` loads them only into a database that has
none yet and never fails the caller: the backend container runs it on every start.
"""

import argparse
import asyncio
import os
import sys

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import get_engine, get_sessionmaker
from app.search.elastic import ElasticErrors
from app.search.reindex import rebuild_search_index
from app.seed.assessment import seed_assessment_bank
from app.seed.fixtures import load_seed_data
from app.seed.loader import (
    DEFAULT_PASSWORD,
    PASSWORD_ENV,
    SeedConflictError,
    SeedSummary,
    demo_data_loaded,
    seed_database,
)


async def _seed(password: str, *, if_missing: bool) -> SeedSummary | None:
    """None when `if_missing` found the demo data already loaded."""
    data = load_seed_data()
    try:
        async with get_sessionmaker()() as session:
            if if_missing and await demo_data_loaded(session, data):
                return None
            summary = await seed_database(session, data, password_hash=hash_password(password))
            # The task bank is not demo data, but a stand without it cannot run a single test.
            await seed_assessment_bank(session)
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
        # On a fresh stack the cluster may still be starting: the API builds the index itself.
        print(
            f"Search index not rebuilt ({exc}); the API builds it on start, "
            "or run `python -m app.search`.",
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
        "--if-missing",
        action="store_true",
        help="load only into a database without demo data; skips (exit 0) otherwise",
    )
    parser.add_argument(
        "--force", action="store_true", help="allow loading demo data with APP_ENV=production"
    )
    args = parser.parse_args(argv)
    # A skipped automatic load must not stop the container start that runs it.
    skipped = 0 if args.if_missing else 1

    if get_settings().is_production and not args.force:
        print("APP_ENV=production: demo data is loaded only with --force", file=sys.stderr)
        return skipped

    password = os.environ.get(PASSWORD_ENV) or DEFAULT_PASSWORD
    try:
        summary = asyncio.run(_seed(password, if_missing=args.if_missing))
    except SeedConflictError as exc:
        print(exc, file=sys.stderr)
        return skipped

    if summary is None:
        print("Demo data is already loaded; run without --if-missing to reload it.")
        return 0
    print(
        f"Demo data loaded: {summary.companies} companies, {summary.vacancies} vacancies, "
        f"{summary.candidates} candidates, {summary.fsp_achievements} FSP results."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
