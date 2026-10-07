"""ORM models. Importing this package registers every table on `Base.metadata` (used by Alembic)."""

import app.admin.models  # noqa: F401  # tables of the admin panel
from app.models.assessment import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentTask,
    AssessmentTest,
)
from app.models.candidate import CandidateProfile
from app.models.candidate_category import CandidateCategory
from app.models.company import Company
from app.models.conversation import Conversation, Message, MessageAttachment
from app.models.email_verification import EmailVerificationCode
from app.models.enums import (
    AssessmentStatus,
    AssignmentStatus,
    AttemptStatus,
    FspDiscipline,
    FspEventLevel,
    Grade,
    InvitationStatus,
    MeetingStatus,
    MessageKind,
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
from app.models.refresh_token import RefreshToken
from app.models.test_assignment import TestAssignment
from app.models.user import User
from app.models.vacancy import Vacancy

__all__ = [
    "AssessmentAnswer",
    "AssessmentAttempt",
    "AssessmentStatus",
    "AssessmentTask",
    "AssessmentTest",
    "AssignmentStatus",
    "AttemptStatus",
    "CandidateCategory",
    "CandidateProfile",
    "CandidateReaction",
    "Company",
    "Conversation",
    "EmailVerificationCode",
    "FspAchievement",
    "FspDiscipline",
    "FspEventLevel",
    "Grade",
    "Invitation",
    "InvitationStatus",
    "Meeting",
    "MeetingStatus",
    "Message",
    "MessageAttachment",
    "MessageKind",
    "ReactionKind",
    "RefreshToken",
    "TaskDifficulty",
    "TaskKind",
    "TestAssignment",
    "User",
    "UserRole",
    "Vacancy",
    "VacancyReaction",
    "WorkFormat",
]
