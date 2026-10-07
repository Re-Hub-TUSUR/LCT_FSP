import uuid
from datetime import datetime

from pydantic import Field

from app.models.enums import UserRole
from app.schemas.common import ApiModel


class UserRead(ApiModel):
    id: uuid.UUID
    email: str
    role: UserRole
    is_email_verified: bool
    created_at: datetime
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None


class UserUpdate(ApiModel):
    """The person behind the account: the recruiter's name and phone (ТЗ, company step 1)."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=32)
