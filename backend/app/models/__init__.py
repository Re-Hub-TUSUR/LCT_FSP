"""ORM models. Importing this package registers every table on `Base.metadata` (used by Alembic)."""

from app.models.assessment import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentTask,
    AssessmentTest,
)
from app.models.candidate import CandidateProfile
from app.models.company import Company
from app.models.email_verification import EmailVerificationCode
from app.models.enums import (
    AssessmentStatus,
    AttemptStatus,
    FspDiscipline,
    FspEventLevel,
    Grade,
    InvitationStatus,
    MeetingStatus,
    ReactionKind,
    TaskDifficulty,
    TaskKind,
    UserRole,
    WorkFormat,
)
from app.models.fsp_achievement import FspAchievement
from app.models.invitation import Invitation
from app.models.meeting import Meeting
from app.models.reaction import CandidateReaction, VacancyReaction
from app.models.user import User
from app.models.vacancy import Vacancy

__all__ = [
    "AssessmentAnswer",
    "AssessmentAttempt",
    "AssessmentStatus",
    "AssessmentTask",
    "AssessmentTest",
    "AttemptStatus",
    "CandidateProfile",
    "CandidateReaction",
    "Company",
    "EmailVerificationCode",
    "FspAchievement",
    "FspDiscipline",
    "FspEventLevel",
    "Grade",
    "Invitation",
    "InvitationStatus",
    "Meeting",
    "MeetingStatus",
    "ReactionKind",
    "TaskDifficulty",
    "TaskKind",
    "User",
    "UserRole",
    "Vacancy",
    "VacancyReaction",
    "WorkFormat",
]
