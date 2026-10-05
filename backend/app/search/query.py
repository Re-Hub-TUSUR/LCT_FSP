"""Elasticsearch request body for a candidate search.

Filters map one-to-one to the database engine. With a vacancy selected, a Painless script computes
`app.services.matching.fit` with the same double arithmetic in the same order, so Elasticsearch
and the database fallback return identical rankings and the match shown on a card is the one the
list is sorted by.
"""

from typing import Any

from app.models import Grade, WorkFormat
from app.search.base import CandidateSearchQuery
from app.search.documents import TEXT_FIELDS
from app.services.matching import (
    GRADES,
    HALF,
    RELOCATION_SHARE,
    SALARY_TOLERANCE,
    WEIGHTS,
    VacancyFacts,
    normalize_term,
    related_specializations,
)

# Mirrors `fit()`: same terms, same order of additions, same half-up rounding to 4 decimals.
# `_score` is the text relevance (0 without a text query), so text matches rank higher.
FIT_SCRIPT = """
double points = params.w_bonus
    * (doc['profile_strength'].size() == 0 ? 0.0 : doc['profile_strength'].value);

String specialization = doc['specialization'].size() == 0 ? '' : doc['specialization'].value;
if (specialization == params.specialization) {
  points += params.w_specialization;
} else if (params.related.contains(specialization)) {
  points += params.w_specialization * params.half;
}

if (doc['grade'].size() != 0) {
  int gap = ((Number) params.grade_index.get(doc['grade'].value)).intValue() - params.grade;
  if (gap == 0) {
    points += params.w_grade;
  } else if (gap == 1 || gap == -1) {
    points += params.w_grade * params.half;
  }
}

if (params.stack.size() > 0) {
  int matched = 0;
  for (String item : params.stack) {
    if (doc['stack'].contains(item)) {
      matched++;
    }
  }
  points += params.w_stack * matched / params.stack.size();
}

if (doc['work_formats'].contains(params.work_format)) {
  points += params.w_work_format;
}

if (params.remote) {
  points += params.w_location;
} else if (params.city != null && doc['city'].size() != 0 && doc['city'].value == params.city) {
  points += params.w_location;
} else if (doc['relocation_ready'].size() != 0 && doc['relocation_ready'].value) {
  points += params.w_location * params.relocation_share;
}

if (doc['salary_expectation'].size() == 0) {
  points += params.w_salary * params.half;
} else {
  long expectation = doc['salary_expectation'].value;
  if (expectation <= params.salary_to) {
    points += params.w_salary;
  } else if (expectation <= params.salary_to * params.salary_tolerance) {
    points += params.w_salary * params.half;
  }
}

return Math.floor((points + _score) * 10000 + 0.5) / 10000;
"""


def _fit_params(vacancy: VacancyFacts) -> dict[str, Any]:
    weights = WEIGHTS
    return {
        "w_bonus": weights.bonus,
        "w_specialization": weights.specialization,
        "w_grade": weights.grade,
        "w_stack": weights.stack,
        "w_work_format": weights.work_format,
        "w_location": weights.location,
        "w_salary": weights.salary,
        "half": HALF,
        "relocation_share": RELOCATION_SHARE,
        "salary_tolerance": SALARY_TOLERANCE,
        "specialization": vacancy.specialization,
        "related": sorted(related_specializations(vacancy.specialization)),
        "grade_index": {grade.value: index for index, grade in enumerate(GRADES)},
        "grade": GRADES.index(vacancy.grade),
        # The index stores technologies and cities normalised; so are the parameters.
        "stack": [normalize_term(item) for item in vacancy.stack],
        "work_format": vacancy.work_format.value,
        "remote": vacancy.work_format == WorkFormat.REMOTE,
        "city": normalize_term(vacancy.city) if vacancy.city else None,
        "salary_to": vacancy.salary_to,
    }


def _filters(query: CandidateSearchQuery) -> list[dict[str, Any]]:
    filters: list[dict[str, Any]] = [
        {"term": {"visible": True}},
        {"term": {"categorized": True}},
    ]
    if query.specialization:
        filters.append({"term": {"specialization": query.specialization}})
    if query.grades:
        filters.append({"terms": {"grade": [Grade(grade).value for grade in query.grades]}})
    # Every listed technology is required; the keyword normaliser makes the terms case-insensitive.
    filters.extend({"term": {"stack": item}} for item in query.stack)
    if query.has_fsp is not None:
        filters.append({"term": {"has_fsp": query.has_fsp}})
    if query.verified_only:
        filters.append({"term": {"verified": True}})
    if query.work_formats:
        filters.append({"terms": {"work_formats": [fmt.value for fmt in query.work_formats]}})
    if query.city:
        filters.append(
            {
                "bool": {
                    "should": [
                        {"term": {"city": query.city}},
                        {"term": {"relocation_ready": True}},
                    ],
                    "minimum_should_match": 1,
                }
            }
        )
    if query.salary_max is not None:
        filters.append(
            {
                "bool": {
                    "should": [
                        {"range": {"salary_expectation": {"lte": query.salary_max}}},
                        {"bool": {"must_not": {"exists": {"field": "salary_expectation"}}}},
                    ],
                    "minimum_should_match": 1,
                }
            }
        )
    if query.experience_min is not None:
        filters.append({"range": {"experience_years": {"gte": query.experience_min}}})
    if query.include_ids is not None:
        filters.append({"ids": {"values": [str(value) for value in query.include_ids]}})
    return filters


def _text(text: str) -> dict[str, Any]:
    """All words across fields first; a typo-tolerant match keeps near misses in the list."""
    return {
        "bool": {
            "should": [
                {
                    "multi_match": {
                        "query": text,
                        "type": "cross_fields",
                        "fields": list(TEXT_FIELDS),
                        "operator": "and",
                        "boost": 2,
                    }
                },
                {
                    "multi_match": {
                        "query": text,
                        "type": "best_fields",
                        "fields": list(TEXT_FIELDS),
                        "fuzziness": "AUTO",
                        "prefix_length": 1,
                    }
                },
            ],
            "minimum_should_match": 1,
        }
    }


_TIE_BREAK: list[dict[str, Any]] = [{"profile_strength": "desc"}, {"id": "asc"}]

_FIELD_SORT: dict[str, dict[str, Any]] = {
    "assessment": {"assessment_score": {"order": "desc", "missing": "_last"}},
    "salary": {"salary_expectation": {"order": "asc", "missing": "_last"}},
    "experience": {"experience_years": {"order": "desc", "missing": "_last"}},
}


def build_search_body(query: CandidateSearchQuery, *, offset: int, limit: int) -> dict[str, Any]:
    base: dict[str, Any] = {"filter": _filters(query)}
    if query.text:
        base["must"] = [_text(query.text)]
    if query.exclude_ids:
        base["must_not"] = [{"ids": {"values": [str(value) for value in query.exclude_ids]}}]
    boolean = {"bool": base}

    if query.sort != "relevance":
        es_query, sort = boolean, [_FIELD_SORT[query.sort], *_TIE_BREAK]
    elif query.vacancy is not None:
        es_query = {
            "function_score": {
                "query": boolean,
                "script_score": {
                    "script": {
                        "lang": "painless",
                        "source": FIT_SCRIPT,
                        "params": _fit_params(query.vacancy),
                    }
                },
                "boost_mode": "replace",
            }
        }
        sort = [{"_score": "desc"}, *_TIE_BREAK]
    elif query.text:
        # Text relevance scaled by profile strength: a strong profile wins among similar matches.
        es_query = {
            "function_score": {
                "query": boolean,
                "functions": [
                    {"field_value_factor": {"field": "profile_strength", "missing": 0}},
                    {"weight": 1},
                ],
                "score_mode": "sum",
                "boost_mode": "multiply",
            }
        }
        sort = [{"_score": "desc"}, *_TIE_BREAK]
    else:
        # Inside a category: the strongest confirmed profile first (ТЗ 2.1).
        es_query, sort = boolean, list(_TIE_BREAK)

    return {
        "query": es_query,
        "sort": sort,
        "from": offset,
        "size": limit,
        "track_total_hits": True,
        "_source": False,
    }
