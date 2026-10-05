import uuid
from datetime import datetime

from app.models.enums import UserRole
from app.schemas.common import ApiModel


class UserRead(ApiModel):
    id: uuid.UUID
    email: str
    role: UserRole
    is_email_verified: bool
    created_at: datetime
