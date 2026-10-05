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
