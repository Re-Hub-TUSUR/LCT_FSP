"""Candidates and jobs as this platform screens them.

An ATS adapter maps its own JSON into these types. Nothing here names a provider.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NormalizedCandidate:
    external_id: str
    name: str
    skills: tuple[str, ...]
    experience_years: int | None
    city: str | None
    salary_expectation: int | None
    resume_text: str | None = None
    resume_bytes: bytes | None = None


@dataclass(frozen=True, slots=True)
class NormalizedJob:
    external_id: str
    title: str
    required_skills: tuple[str, ...]
    salary_from: int | None
    salary_to: int | None
    city: str | None


@dataclass(frozen=True, slots=True)
class NormalizedApplication:
    external_id: str
    candidate: NormalizedCandidate
    job: NormalizedJob


@dataclass(frozen=True, slots=True)
class PollChange:
    """One application the provider says is new or still current since the cursor."""

    external_event_id: str
    raw: dict[str, object]
    application: NormalizedApplication


@dataclass(frozen=True, slots=True)
class PollPage:
    changes: tuple[PollChange, ...]
    next_cursor: str


@dataclass(frozen=True, slots=True)
class AtsRecord:
    kind: str
    value: str
