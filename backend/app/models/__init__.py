"""ORM models. Importing this package registers every table on `Base.metadata` (used by Alembic)."""

from app.models.candidate import CandidateProfile
from app.models.company import Company
from app.models.enums import Grade, InvitationStatus, UserRole, WorkFormat
from app.models.invitation import Invitation
from app.models.user import User
from app.models.vacancy import Vacancy

__all__ = [
    "CandidateProfile",
    "Company",
    "Grade",
    "Invitation",
    "InvitationStatus",
    "User",
    "UserRole",
    "Vacancy",
    "WorkFormat",
]
