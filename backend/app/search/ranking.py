"""Candidate ordering shared by the engines: the Elasticsearch query reproduces exactly this."""

from collections.abc import Callable

from app.models import CandidateProfile
from app.search.base import CandidateSearchQuery
from app.services.matching import CandidateFacts, fit

# Sort key for one profile; smaller sorts first.
SortKey = tuple[float, float, str]


def _strength(profile: CandidateProfile) -> float:
    return CandidateFacts.of(profile).strength


def sort_key(query: CandidateSearchQuery) -> Callable[[CandidateProfile], SortKey]:
    """Ties are broken by profile strength, then by id, in every order."""

    def relevance(profile: CandidateProfile) -> SortKey:
        facts = CandidateFacts.of(profile)
        if query.vacancy is None:
            return (-facts.strength, 0.0, str(profile.id))
        points = fit(facts, query.vacancy, bonus=facts.strength).points
        return (-points, -facts.strength, str(profile.id))

    def assessment(profile: CandidateProfile) -> SortKey:
        score = profile.assessment_score
        return (-(score if score is not None else -1.0), -_strength(profile), str(profile.id))

    def salary(profile: CandidateProfile) -> SortKey:
        expectation = profile.salary_expectation
        missing = float("inf")
        return (
            float(expectation) if expectation is not None else missing,
            -_strength(profile),
            str(profile.id),
        )

    def experience(profile: CandidateProfile) -> SortKey:
        years = profile.experience_years
        return (-(years if years is not None else -1), -_strength(profile), str(profile.id))

    return {
        "relevance": relevance,
        "assessment": assessment,
        "salary": salary,
        "experience": experience,
    }[query.sort]
