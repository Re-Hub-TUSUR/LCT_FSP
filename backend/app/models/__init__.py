"""ORM models. Importing this package registers every table on `Base.metadata` (used by Alembic)."""

from app.models.candidate import CandidateProfile
from app.models.company import Company
from app.models.email_verification import EmailVerificationCode
from app.models.enums import (
    FspDiscipline,
    FspEventLevel,
    Grade,
    InvitationStatus,
    UserRole,
    WorkFormat,
)
from app.models.fsp_achievement import FspAchievement
from app.models.invitation import Invitation
from app.models.user import User
from app.models.vacancy import Vacancy

__all__ = [
    "CandidateProfile",
    "Company",
    "EmailVerificationCode",
    "FspAchievement",
    "FspDiscipline",
    "FspEventLevel",
    "Grade",
    "Invitation",
    "InvitationStatus",
    "User",
    "UserRole",
    "Vacancy",
    "WorkFormat",
]
