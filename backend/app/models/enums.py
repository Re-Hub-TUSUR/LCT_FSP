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


class WorkFormat(StrEnum):
    OFFICE = "office"
    HYBRID = "hybrid"
    REMOTE = "remote"


class InvitationStatus(StrEnum):
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
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
