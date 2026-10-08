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
from app.search.ranking import sort_key
from app.search.synonyms import alternatives
from app.services.matching import fsp_search_text, normalize_term
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
        fsp_search_text(profile),
    )
    return normalize(" ".join(part for part in parts if part))


def matches_text(profile: CandidateProfile, text: str) -> bool:
    haystack = searchable_text(profile)
    return all(
        any(alternative in haystack for alternative in alternatives(token))
        for token in tokens(text)
    )


def matches(profile: CandidateProfile, query: CandidateSearchQuery) -> bool:
    """The filters the SQL query could not apply, compared like the search index compares them."""
    owned = {normalize_term(item) for item in profile.stack}
    if any(normalize_term(item) not in owned for item in query.stack):
        return False
    if query.work_formats and not set(profile.work_formats) & set(query.work_formats):
        return False
    if query.city is not None:
        same_city = profile.city is not None and normalize_term(profile.city) == normalize_term(
            query.city
        )
        if not (same_city or profile.relocation_ready):
            return False
    return not (query.text and not matches_text(profile, query.text))


class DatabaseCandidateSearch:
    name: SearchEngine = "database"

    def __init__(self, candidates: CandidateRepository) -> None:
        self._candidates = candidates

    async def search(self, query: CandidateSearchQuery, *, offset: int, limit: int) -> SearchHits:
        profiles = await self._candidates.searchable(
            specialization=query.specialization,
            grades=query.grades,
            has_fsp=query.has_fsp,
            verified_only=query.verified_only,
            salary_max=query.salary_max,
            experience_min=query.experience_min,
            include_ids=query.include_ids,
            exclude_ids=query.exclude_ids,
        )
        found = sorted((p for p in profiles if matches(p, query)), key=sort_key(query))
        return SearchHits(ids=[p.id for p in found[offset : offset + limit]], total=len(found))
