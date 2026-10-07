"""Candidate search on the database: the fallback when Elasticsearch is off or unreachable.

Structured filters run in SQL; JSON columns, the city and the text are checked in Python. Text
matching is a plain substring check with IT synonyms: no morphology and no relevance score, so
with a text query the order is by profile strength. Fine for tests and small installations.
"""

import re
from collections.abc import Iterable

from app.models import CandidateProfile
from app.repositories.candidate import CandidateRepository
from app.schemas.candidate import SearchEngine
from app.search.base import CandidateSearchQuery, SearchHits
from app.search.filters import FilterFacts, passes
from app.search.ranking import sort_key
from app.search.synonyms import alternatives
from app.services.presenters import profile_category

_TOKEN = re.compile(r"[\w.+#-]+")


def normalize(text: str) -> str:
    return text.casefold().replace("ё", "е")


def tokens(text: str) -> list[str]:
    return [token.strip(".-") for token in _TOKEN.findall(normalize(text)) if token.strip(".-")]


def searchable_text(profile: CandidateProfile) -> str:
    """Everything a recruiter may type a word from; achievements must be loaded."""
    category = profile_category(profile)
    parts: Iterable[str | None] = (
        profile.display_name,
        profile.headline,
        profile.about,
        " ".join(profile.stack),
        " ".join(profile.soft_skills),
        profile.city,
        category.label if category else None,
        " ".join(item.event_name for item in profile.fsp_achievements),
    )
    return normalize(" ".join(part for part in parts if part))


def matches_text(profile: CandidateProfile, text: str) -> bool:
    haystack = searchable_text(profile)
    return all(
        any(alternative in haystack for alternative in alternatives(token))
        for token in tokens(text)
    )


def matches(profile: CandidateProfile, query: CandidateSearchQuery) -> bool:
    """Every structured filter as `app.search.filters` defines it, then the text."""
    if not passes(FilterFacts.of(profile), query):
        return False
    return not (query.text and not matches_text(profile, query.text))


class DatabaseCandidateSearch:
    name: SearchEngine = "database"

    def __init__(self, candidates: CandidateRepository) -> None:
        self._candidates = candidates

    async def search(self, query: CandidateSearchQuery, *, offset: int, limit: int) -> SearchHits:
        profiles = await self._candidates.searchable(
            specializations=query.specializations,
            grades=query.grades,
            verified_only=query.verified_only,
            experience_min=query.experience_min,
            include_ids=query.include_ids,
            exclude_ids=query.exclude_ids,
        )
        found = sorted((p for p in profiles if matches(p, query)), key=sort_key(query))
        return SearchHits(ids=[p.id for p in found[offset : offset + limit]], total=len(found))
