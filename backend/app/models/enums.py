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

    @property
    def following(self) -> "Grade | None":
        """The grade one step up; the top one has none."""
        grades = list(Grade)
        position = grades.index(self) + 1
        return grades[position] if position < len(grades) else None


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
    # Finished, but some answers wait for a person to grade them (employer's tests only).
    AWAITING_REVIEW = "awaiting_review"
    # Finished, but the code runner was down: the answers are frozen and graded once it is back.
    GRADING = "grading"
    # Passed on points with working code: the AI interviewer asks about that code, and the grade
    # is confirmed once the answers show understanding (`app.services.interview`).
    INTERVIEW = "interview"


class TaskKind(StrEnum):
    """Behaviour of every kind is described in `app.services.task_kinds`."""

    QUIZ = "quiz"
    CODE = "code"
    OPEN = "open"


class AssignmentStatus(StrEnum):
    """Life of a test a company sent to a candidate."""

    SENT = "sent"
    IN_PROGRESS = "in_progress"
    # Taken; open answers wait for the company's grades.
    REVIEW = "review"
    DONE = "done"
    DECLINED = "declined"
    # Not started before the due date.
    EXPIRED = "expired"


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


class MessageKind(StrEnum):
    TEXT = "text"
    ATTACHMENT = "attachment"
    MEETING = "meeting"
