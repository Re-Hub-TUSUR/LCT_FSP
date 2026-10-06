from app.core.config import Settings
from app.db.session import get_sessionmaker
from app.repositories.candidate import CandidateRepository
from app.search.elastic import CandidateIndex, create_client


async def rebuild_search_index(settings: Settings) -> int | None:
    """Rebuilds the candidate index from the database; None when Elasticsearch is off.

    Run after bulk changes (demo data load); single profile updates use `CandidateIndex.upsert`.
    """
    if not settings.elasticsearch_url:
        return None
    async with get_sessionmaker()() as session:
        profiles = await CandidateRepository(session).all()
    client = create_client(settings)
    try:
        return await CandidateIndex(client, settings.elasticsearch_index).rebuild(profiles)
    finally:
        await client.close()
