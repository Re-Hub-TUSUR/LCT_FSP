from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Base for public API schemas: camelCase on the wire, snake_case in Python."""

    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True, from_attributes=True)


class ErrorBody(ApiModel):
    code: str
    message: str
    details: Any = None


class ErrorResponse(ApiModel):
    error: ErrorBody


class Page[T](ApiModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class SalaryRange(ApiModel):
    """Mandatory "from–to" salary range in RUB (ТЗ 2.2, item 1)."""

    from_: int = Field(alias="from", gt=0)
    to: int = Field(gt=0)

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        if self.from_ > self.to:
            msg = "salary.from must not exceed salary.to"
            raise ValueError(msg)
        return self


ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Не авторизован"},
    403: {"model": ErrorResponse, "description": "Недостаточно прав"},
    422: {"model": ErrorResponse, "description": "Ошибка валидации"},
    501: {"model": ErrorResponse, "description": "Метод ещё не реализован"},
}
