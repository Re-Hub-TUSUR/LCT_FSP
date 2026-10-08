from pydantic import Field

from app.models.enums import Grade
from app.schemas.common import ApiModel


class Category(ApiModel):
    """Group of comparable candidates: specialization + grade."""

    code: str
    label: str
    specialization: str
    grade: Grade


class SpecializationRead(ApiModel):
    code: str
    label: str


class GradeRead(ApiModel):
    code: Grade
    label: str


class CategoryDictionary(ApiModel):
    specializations: list[SpecializationRead]
    grades: list[GradeRead]
    # IT slang the search understands, lowercase: the first word of a group is the usual one
    # (`python`, `питон`, `пайтон`). The filters use it to find «Python» by «питон».
    synonyms: list[list[str]] = Field(default_factory=list)
