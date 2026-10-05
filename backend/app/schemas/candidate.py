import uuid

from pydantic import Field

from app.models.enums import Grade
from app.schemas.category import Category
from app.schemas.common import ApiModel


class FspAchievement(ApiModel):
    event_name: str
    year: int
    place: int | None
    discipline: str


class CandidateContacts(ApiModel):
    email: str
    phone: str | None
    telegram: str | None


class CandidateRead(ApiModel):
    id: uuid.UUID
    display_name: str
    headline: str | None
    category: Category | None
    stack: list[str]
    experience_years: int | None
    assessment_score: float | None
    # Empty list = no FSP history; must be handled explicitly (ТЗ, section 2).
    fsp_achievements: list[FspAchievement]
    fsp_linked: bool
    # Revealed only after the candidate accepted an invitation or applied (ТЗ 2.2, item 2).
    contacts: CandidateContacts | None


class CandidateProfileUpdate(ApiModel):
    display_name: str | None = Field(default=None, max_length=200)
    headline: str | None = Field(default=None, max_length=300)
    about: str | None = None
    stack: list[str] | None = None
    experience_years: int | None = Field(default=None, ge=0, le=60)
    is_visible_to_employers: bool | None = None


class CandidateSearchFilters(ApiModel):
    specialization: str | None = None
    grade: Grade | None = None
    stack: list[str] = Field(default_factory=list)
    has_fsp_achievements: bool | None = None


class FspLinkRequest(ApiModel):
    fsp_member_id: str = Field(min_length=1, max_length=64)
