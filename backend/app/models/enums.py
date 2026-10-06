from enum import StrEnum


class UserRole(StrEnum):
    CANDIDATE = "candidate"
    EMPLOYER = "employer"
    ADMIN = "admin"


class Grade(StrEnum):
    INTERN = "intern"
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"
    LEAD = "lead"


class AssessmentStatus(StrEnum):
    """Outcome of the platform grade test as employers see it."""

    NOT_TAKEN = "not_taken"
    PASSED = "passed"
    FAILED = "failed"


class AttemptStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    # Abandoned: the time ran out and the candidate never finished it.
    EXPIRED = "expired"


class TaskKind(StrEnum):
    QUIZ = "quiz"
    CODE = "code"


class TaskDifficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class WorkFormat(StrEnum):
    OFFICE = "office"
    HYBRID = "hybrid"
    REMOTE = "remote"


class InvitationStatus(StrEnum):
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class MeetingStatus(StrEnum):
    """The candidate's answer to a meeting the company scheduled."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    DECLINED = "declined"


class FspDiscipline(StrEnum):
    """Disciplines of sport programming held by FSP."""

    ALGORITHMIC = "algorithmic"
    PRODUCT = "product"
    SECURITY = "security"
    ROBOTICS = "robotics"
    UAV = "uav"


class FspEventLevel(StrEnum):
    REGIONAL = "regional"
    NATIONAL = "national"
    INTERNATIONAL = "international"


class ReactionKind(StrEnum):
    """Decision on a feed card: `like` keeps it in favourites, `skip` hides it from the feed."""

    LIKE = "like"
    SKIP = "skip"
