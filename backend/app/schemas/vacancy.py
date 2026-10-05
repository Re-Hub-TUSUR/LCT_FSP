import uuid
from datetime import datetime

from pydantic import Field

from app.models.enums import Grade, WorkFormat
from app.schemas.category import Category
from app.schemas.common import ApiModel, SalaryRange


class CompanyRef(ApiModel):
    id: uuid.UUID
    name: str


class VacancyRead(ApiModel):
    id: uuid.UUID
    title: str
    company: CompanyRef
    category: Category
    stack: list[str]
    salary: SalaryRange
    work_format: WorkFormat
    published_at: datetime


class VacancyCreate(ApiModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=20)
    specialization: str
    grade: Grade
    stack: list[str] = Field(default_factory=list)
    salary: SalaryRange
    work_format: WorkFormat
