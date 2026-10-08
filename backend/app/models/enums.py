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


class EmploymentType(StrEnum):
    FULL = "full"
    PART = "part"
    PROJECT = "project"
    INTERNSHIP = "internship"


class JobStatus(StrEnum):
    """The candidate's own answer to «are you looking»; `not_looking` hides them from search."""

    ACTIVE = "active"
    OPEN = "open"
    NOT_LOOKING = "not_looking"


class FspSync(StrEnum):
    """Answer to «Синхронизировать с ФСП?» on the resume start screen."""

    YES = "yes"
    LATER = "later"
    NEVER = "never"


class FspResult(StrEnum):
    """Best FSP result a vacancy asks for, derived from the place in the registry."""

    PARTICIPANT = "participant"
    FINALIST = "finalist"
    PRIZEWINNER = "prizewinner"


class VacancyBenefit(StrEnum):
    DMS = "dms"
    FLEXIBLE_START = "flexible_start"
    LABOR_CODE = "labor_code"


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


class FspEventKind(StrEnum):
    CHAMPIONSHIP = "championship"
    CUP = "cup"
    HACKATHON = "hackathon"
    OLYMPIAD = "olympiad"


class FspOutcome(StrEnum):
    """Result of one FSP event as the registry names it; ordered from the best."""

    WINNER = "winner"
    PRIZEWINNER = "prizewinner"
    FINALIST = "finalist"
    PARTICIPANT = "participant"

    @classmethod
    def from_place(cls, place: int | None) -> "FspOutcome":
        if place is None:
            return cls.PARTICIPANT
        if place == 1:
            return cls.WINNER
        if place <= 3:  # noqa: PLR2004 - podium
            return cls.PRIZEWINNER
        return cls.FINALIST


class FspParticipation(StrEnum):
    INDIVIDUAL = "individual"
    TEAM = "team"


class FspTitleKind(StrEnum):
    """Sport ranks (разряды) and titles (звания) of sport programming, from the lowest."""

    RANK_3 = "rank_3"
    RANK_2 = "rank_2"
    RANK_1 = "rank_1"
    KMS = "kms"
    MS = "ms"
    MSMK = "msmk"
    ZMS = "zms"


class ReactionKind(StrEnum):
    """Decision on a feed card: `like` keeps it in favourites, `skip` hides it from the feed."""

    LIKE = "like"
    SKIP = "skip"


class SavedSearchKind(StrEnum):
    """What a saved search finds: a recruiter's candidates or a candidate's vacancies."""

    CANDIDATES = "candidates"
    VACANCIES = "vacancies"


class MessageKind(StrEnum):
    TEXT = "text"
    ATTACHMENT = "attachment"
    MEETING = "meeting"
