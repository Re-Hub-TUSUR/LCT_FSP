"""Turns an uploaded resume into a draft of the profile form. Neither the file nor the draft is
stored: the candidate checks the fields and saves them with the usual form."""

import asyncio
import base64
from collections.abc import Collection

from app.core.errors import AppError
from app.models.enums import WorkFormat
from app.schemas.candidate import ResumeDraft
from app.services.candidates import MAX_SKILL_LENGTH
from app.services.categories import SPECIALIZATIONS
from app.services.resume_photo import resume_photo
from app.services.resume_reader import ResumeReader
from app.services.resume_text import ResumeText, read_resume
from app.services.uploads import RESUME_LIMIT

MAX_EXPERIENCE_YEARS = 50


class ResumeImportService:
    def __init__(self, reader: ResumeReader) -> None:
        self._reader = reader

    async def draft(self, data: bytes) -> ResumeDraft:
        if len(data) > RESUME_LIMIT:
            raise AppError("Файл больше 5 МБ")
        # Parsing a PDF is CPU work: keep it off the event loop.
        document, photo = await asyncio.to_thread(_read, data)
        fields = await self._reader.read(document.text)
        return ResumeDraft(
            display_name=_text(fields.get("display_name"), limit=200),
            headline=_text(fields.get("headline"), limit=300),
            specialization=_choice(fields.get("specialization"), SPECIALIZATIONS),
            city=_text(fields.get("city"), limit=100),
            experience_years=_whole(fields.get("experience_years"), upper=MAX_EXPERIENCE_YEARS),
            work_formats=_formats(fields.get("work_formats")),
            stack=_items(fields.get("stack"), limit=30),
            soft_skills=_items(fields.get("soft_skills"), limit=20),
            about=_text(fields.get("about"), limit=2000),
            salary_expectation=_whole(fields.get("salary_expectation"), lower=1),
            # Contacts never reach the model: they are found in the file itself.
            phone=document.phone,
            telegram=document.telegram,
            photo=base64.b64encode(photo).decode("ascii") if photo else None,
        )


def _read(data: bytes) -> tuple[ResumeText, bytes | None]:
    # The text first: a file that is not a resume is refused before its pictures are opened.
    return read_resume(data), resume_photo(data)


def _text(value: object, *, limit: int) -> str | None:
    if not isinstance(value, str):
        return None
    return " ".join(value.split())[:limit] or None


def _choice(value: object, options: Collection[str]) -> str | None:
    return value if isinstance(value, str) and value in options else None


def _whole(value: object, *, lower: int = 0, upper: int | None = None) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    number = int(value)
    if number < lower or (upper is not None and number > upper):
        return None
    return number


def _formats(value: object) -> list[WorkFormat]:
    if not isinstance(value, list):
        return []
    known = {item.value: item for item in WorkFormat}
    return list(
        dict.fromkeys(known[item] for item in value if isinstance(item, str) and item in known)
    )


def _items(value: object, *, limit: int) -> list[str]:
    """The same rules as the form: trimmed, no duplicates, nothing longer than a skill may be."""
    if not isinstance(value, list):
        return []
    items: list[str] = []
    seen: set[str] = set()
    for raw in value:
        if not isinstance(raw, str):
            continue
        item = " ".join(raw.split())
        key = item.casefold()
        if not item or len(item) > MAX_SKILL_LENGTH or key in seen:
            continue
        seen.add(key)
        items.append(item)
    return items[:limit]
