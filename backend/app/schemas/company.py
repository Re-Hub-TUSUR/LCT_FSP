import uuid

from pydantic import EmailStr, Field, HttpUrl

from app.schemas.common import ApiModel


class CompanyRead(ApiModel):
    id: uuid.UUID
    name: str
    industry: str | None
    description: str | None
    city: str | None
    # Headcount bucket, e.g. "201–500".
    size: str | None
    website: str | None
    contact_email: str | None


class CompanyUpsert(ApiModel):
    name: str = Field(min_length=1, max_length=200)
    industry: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=100, max_length=3000)
    city: str = Field(min_length=1, max_length=100)
    size: str | None = Field(default=None, max_length=16)
    website: HttpUrl
    contact_email: EmailStr
