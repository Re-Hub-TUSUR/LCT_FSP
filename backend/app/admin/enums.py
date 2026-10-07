from enum import StrEnum


class TaskStatus(StrEnum):
    """Life of a bank task. Only `active` tasks reach candidates (mirrored into `is_active`)."""

    DRAFT = "draft"
    ACTIVE = "active"
    LEAKED = "leaked"
    ARCHIVED = "archived"


class EmployerCaseStatus(StrEnum):
    """Admin's decision on a company the signals pointed at."""

    FLAGGED = "flagged"
    CLEARED = "cleared"
    WARNED = "warned"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"


class VerificationStatus(StrEnum):
    """Check of the documents a company uploaded to prove it is real."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AnalyticsPeriod(StrEnum):
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"
    ALL = "all"

    @property
    def days(self) -> int | None:
        return {"7d": 7, "30d": 30, "90d": 90}.get(self.value)
