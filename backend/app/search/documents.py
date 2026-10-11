"""Elasticsearch index definition and the document built from a candidate profile."""

import hashlib
import json
from typing import Any, Final

from app.models import CandidateProfile
from app.search.filters import fsp_marks
from app.search.synonyms import elasticsearch_rules
from app.services.matching import CandidateFacts, as_utc, fsp_search_text
from app.services.presenters import profile_category

# Russian morphology (stemming) at index and search time; IT slang synonyms at search time only,
# so the synonym list can change without reindexing. «ё» and «е» are the same letter for search.
SETTINGS: dict[str, Any] = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
        "char_filter": {"yo": {"type": "mapping", "mappings": ["ё => е", "Ё => Е"]}},
        "normalizer": {"lower": {"type": "custom", "char_filter": ["yo"], "filter": ["lowercase"]}},
        "filter": {
            "ru_stop": {"type": "stop", "stopwords": "_russian_"},
            "ru_stemmer": {"type": "stemmer", "language": "russian"},
            "it_synonyms": {
                "type": "synonym_graph",
                "synonyms": elasticsearch_rules(),
                "lenient": True,
            },
        },
        "analyzer": {
            "ru_text": {
                "type": "custom",
                "tokenizer": "standard",
                "char_filter": ["yo"],
                "filter": ["lowercase", "ru_stop", "ru_stemmer"],
            },
            "ru_search": {
                "type": "custom",
                "tokenizer": "standard",
                "char_filter": ["yo"],
                "filter": ["lowercase", "it_synonyms", "ru_stop", "ru_stemmer"],
            },
        },
    },
}

_TEXT: dict[str, Any] = {"type": "text", "analyzer": "ru_text", "search_analyzer": "ru_search"}
_KEYWORD_WITH_TEXT: dict[str, Any] = {
    "type": "keyword",
    "normalizer": "lower",
    "fields": {"text": _TEXT},
}

MAPPINGS: dict[str, Any] = {
    "dynamic": "strict",
    "properties": {
        "id": {"type": "keyword"},
        "display_name": _TEXT,
        "headline": _TEXT,
        "about": _TEXT,
        "category_label": _TEXT,
        "stack": _KEYWORD_WITH_TEXT,
        "soft_skills": _TEXT,
        "city": _KEYWORD_WITH_TEXT,
        "city_id": {"type": "integer"},
        "fsp_text": _TEXT,
        "specialization": {"type": "keyword"},
        # Professions of the additional resumes: they score in the vacancy fit, not in filters.
        "other_specializations": {"type": "keyword"},
        "grade": {"type": "keyword"},
        "experience_years": {"type": "integer"},
        "relocation_ready": {"type": "boolean"},
        "work_formats": {"type": "keyword"},
        "salary_expectation": {"type": "integer"},
        "english_level": {"type": "keyword"},
        "assessment_score": {"type": "double"},
        "verified": {"type": "boolean"},
        # The grade was confirmed by a beta test and is provisional.
        "grade_beta": {"type": "boolean"},
        "assessment_status": {"type": "keyword"},
        "has_fsp": {"type": "boolean"},
        # `discipline:result` terms, see `app.search.filters.fsp_marks`.
        "fsp_marks": {"type": "keyword"},
        "employment_types": {"type": "keyword"},
        "job_status": {"type": "keyword"},
        "last_active_at": {"type": "date"},
        "profile_strength": {"type": "double"},
        # Hidden and not yet categorised profiles are indexed but never returned to recruiters.
        "visible": {"type": "boolean"},
        "categorized": {"type": "boolean"},
    },
}

# Fingerprint of the index definition. An index built from another definition is rebuilt on the
# first search, so a new field reaches the cluster without a manual reindex.
INDEX_VERSION: Final = hashlib.sha256(
    json.dumps([SETTINGS, MAPPINGS], sort_keys=True, ensure_ascii=False).encode()
).hexdigest()[:12]

# Fields of the free-text query and their weights.
TEXT_FIELDS: tuple[str, ...] = (
    "headline^3",
    "stack.text^3",
    "category_label^2",
    "display_name^2",
    "about",
    "soft_skills",
    "city.text",
    "fsp_text",
)


def candidate_document(profile: CandidateProfile) -> dict[str, Any]:
    """`profile.fsp_achievements` and `profile.fsp_titles` must be loaded."""
    category = profile_category(profile)
    facts = CandidateFacts.of(profile)
    fsp_text = fsp_search_text(profile)
    return {
        "id": str(profile.id),
        "display_name": profile.display_name,
        "headline": profile.headline,
        "about": profile.about,
        "category_label": category.label if category else None,
        "stack": list(profile.stack),
        "soft_skills": list(profile.soft_skills),
        "city": profile.city,
        "city_id": profile.city_id,
        "fsp_text": fsp_text or None,
        "specialization": profile.specialization,
        "other_specializations": list(facts.other_specializations),
        "grade": profile.grade.value if profile.grade else None,
        "experience_years": profile.experience_years,
        "relocation_ready": profile.relocation_ready,
        "work_formats": list(profile.work_formats),
        "salary_expectation": profile.salary_expectation,
        "english_level": profile.english_level,
        "assessment_score": profile.assessment_score,
        "verified": profile.assessment_score is not None,
        "grade_beta": profile.assessment_beta,
        "assessment_status": profile.assessment_status.value,
        "has_fsp": bool(profile.fsp_achievements),
        "fsp_marks": sorted(fsp_marks(profile.fsp_achievements)),
        "employment_types": list(profile.employment_types),
        "job_status": profile.job_status.value,
        "last_active_at": as_utc(profile.last_active_at).isoformat()
        if profile.last_active_at
        else None,
        "profile_strength": facts.strength,
        "visible": profile.is_visible_to_employers,
        "categorized": category is not None,
    }
