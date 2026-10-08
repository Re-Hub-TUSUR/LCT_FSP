"""Replaceable screening. Adapters never call this: they only deliver a normalized pair.

Stages do not know each other. A later embeddings or LLM stage replaces the empty one
without a change to the ATS adapters.
"""

from dataclasses import dataclass, field
from typing import Protocol

from app.integrations.ats.normalized import NormalizedCandidate, NormalizedJob
from app.models.enums import ScreeningDecision

MODEL_VERSION = "rules-1"
_PASS_AT = 70


@dataclass(slots=True)
class ScreeningState:
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    score: int = 0
    decision: ScreeningDecision = ScreeningDecision.REVIEW
    hard_failed: bool = False
    model_version: str = MODEL_VERSION


class ScreeningStage(Protocol):
    def apply(
        self, candidate: NormalizedCandidate, job: NormalizedJob, state: ScreeningState
    ) -> None: ...


class ScreeningPipeline:
    def __init__(self, stages: tuple[ScreeningStage, ...] | list[ScreeningStage]) -> None:
        self._stages = tuple(stages)

    def run(self, candidate: NormalizedCandidate, job: NormalizedJob) -> ScreeningState:
        state = ScreeningState()
        for stage in self._stages:
            stage.apply(candidate, job, state)
        return state


class HardFilters:
    """Required skills, the salary ceiling and the city. These are our vacancy fields."""

    def apply(
        self, candidate: NormalizedCandidate, job: NormalizedJob, state: ScreeningState
    ) -> None:
        have = {_key(skill) for skill in candidate.skills}
        state.matched_skills = [skill for skill in job.required_skills if _key(skill) in have]
        state.missing_skills = [skill for skill in job.required_skills if _key(skill) not in have]
        if state.missing_skills:
            state.hard_failed = True
            state.reasons.append(f"Нет обязательных навыков: {', '.join(state.missing_skills)}")
        if _differs(candidate.city, job.city):
            state.hard_failed = True
            state.reasons.append(f"Город {candidate.city} не совпадает с {job.city}")
        if (
            job.salary_to is not None
            and candidate.salary_expectation is not None
            and candidate.salary_expectation > job.salary_to
        ):
            state.hard_failed = True
            state.reasons.append("Ожидание по зарплате выше вилки")


class ScoreRules:
    def apply(
        self, candidate: NormalizedCandidate, job: NormalizedJob, state: ScreeningState
    ) -> None:
        required = len(job.required_skills)
        ratio = len(state.matched_skills) / required if required else 1
        score = round(ratio * 80)
        if job.city and candidate.city and not _differs(candidate.city, job.city):
            score += 10
            state.reasons.append(f"Город совпадает: {candidate.city}")
        if _salary_inside(candidate, job):
            score += 10
            state.reasons.append("Ожидание по зарплате внутри вилки")
        if state.matched_skills:
            state.reasons.append(f"Совпали навыки: {', '.join(state.matched_skills)}")
        state.score = min(100, score)
        if state.hard_failed:
            state.decision = ScreeningDecision.REJECT
        elif state.score >= _PASS_AT:
            state.decision = ScreeningDecision.PASSED
        else:
            state.decision = ScreeningDecision.REVIEW
        state.model_version = MODEL_VERSION


class NullEmbeddings:
    """Slot for a later vector stage. It does not change the score."""

    def apply(
        self, candidate: NormalizedCandidate, job: NormalizedJob, state: ScreeningState
    ) -> None:
        # The arguments are the stage contract. This slot does not read them yet.
        del candidate, job, state


class NullLlm:
    """Slot for a later model stage. The resume parser keeps its own RouterAI key."""

    def apply(
        self, candidate: NormalizedCandidate, job: NormalizedJob, state: ScreeningState
    ) -> None:
        del candidate, job, state


def default_pipeline() -> ScreeningPipeline:
    return ScreeningPipeline((HardFilters(), ScoreRules(), NullEmbeddings(), NullLlm()))


def _key(skill: str) -> str:
    return " ".join(skill.casefold().split())


def _differs(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    return _key(left) != _key(right)


def _salary_inside(candidate: NormalizedCandidate, job: NormalizedJob) -> bool:
    expectation = candidate.salary_expectation
    if expectation is None:
        return False
    if job.salary_from is not None and expectation < job.salary_from:
        return False
    if job.salary_to is not None and expectation > job.salary_to:
        return False
    return job.salary_from is not None or job.salary_to is not None
