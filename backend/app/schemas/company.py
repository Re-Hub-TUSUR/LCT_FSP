import re
import uuid
from typing import Literal

from pydantic import EmailStr, Field, HttpUrl, field_validator

from app.schemas.common import ApiModel
from app.services.inn import is_valid_inn

_DIGITS = re.compile(r"\d+")

# Headcount buckets of the company form; nothing else is stored.
CompanySize = Literal["1-10", "11-50", "51-200", "201-500", "500+"]


class CompanyRead(ApiModel):
    id: uuid.UUID
    name: str
    industry: str | None
    description: str | None
    city: str | None
    # Headcount bucket, one of `CompanySize`.
    size: str | None
    website: str | None
    contact_email: str | None
    inn: str | None = None
    ogrn: str | None = None
    kpp: str | None = None
    legal_address: str | None = None
    has_logo: bool = False
    # An admin approved the Минцифры registry extract.
    it_accredited: bool = False


def _digits(value: str | None, lengths: tuple[int, ...], label: str) -> str | None:
    if value is None:
        return None
    text = "".join(value.split())
    if not text:
        return None
    if not _DIGITS.fullmatch(text) or len(text) not in lengths:
        allowed = " или ".join(str(length) for length in lengths)
        msg = f"{label}: {allowed} цифр"
        raise ValueError(msg)
    return text


class CompanyUpsert(ApiModel):
    # Shown to candidates; may differ from the legal name.
    name: str = Field(min_length=1, max_length=200)
    industry: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=100, max_length=3000)
    city: str = Field(min_length=1, max_length=100)
    size: CompanySize | None = None
    website: HttpUrl
    contact_email: EmailStr
    inn: str = Field(min_length=10, max_length=14)
    ogrn: str | None = Field(default=None, max_length=17)
    kpp: str | None = Field(default=None, max_length=11)
    legal_address: str | None = Field(default=None, max_length=500)

    @field_validator("size", mode="before")
    @classmethod
    def _size(cls, value: object) -> object:
        # The form sends an empty string for «Не указан».
        return value or None

    @field_validator("inn")
    @classmethod
    def _inn(cls, value: str) -> str:
        text = "".join(value.split())
        if not is_valid_inn(text):
            msg = "ИНН: 10 или 12 цифр с верной контрольной суммой"
            raise ValueError(msg)
        return text

    @field_validator("ogrn")
    @classmethod
    def _ogrn(cls, value: str | None) -> str | None:
        return _digits(value, (13, 15), "ОГРН")

    @field_validator("kpp")
    @classmethod
    def _kpp(cls, value: str | None) -> str | None:
        return _digits(value, (9,), "КПП")
