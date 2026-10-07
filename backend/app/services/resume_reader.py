"""Reads resume fields with a language model on RouterAI (`app.services.llm`).

Plug-in point: set `ROUTERAI_API_KEY`; `RESUME_PARSER_MODEL` picks the model. Swap the provider
by implementing `ResumeReader`.
"""

from typing import Any, Final, Protocol

from app.core.errors import ServiceUnavailableError
from app.models.enums import WorkFormat
from app.services.categories import SPECIALIZATIONS
from app.services.llm import JsonModel, LlmUnavailableError
from app.services.resume_text import HIDDEN

# The JSON answer is under 1 000 tokens.
_MAX_TOKENS: Final = 1500

_SPECIALIZATION_LIST = "; ".join(f"{code} — {label}" for code, label in SPECIALIZATIONS.items())

INSTRUCTIONS: Final = f"""Ты переносишь резюме ИТ-специалиста в анкету платформы подбора.
Верни только JSON по схеме. Чего нет в резюме — null или пустой список, ничего не придумывай.
- display_name: имя и фамилия, как в резюме.
- headline: желаемая должность или текущая роль, коротко, например «Python-разработчик».
- specialization: код ближайшей специализации по основной роли: {_SPECIALIZATION_LIST}.
- experience_years: полных лет опыта работы в ИТ (сумма периодов работы, без учёбы).
- city: город проживания по-русски, без страны.
- work_formats: какие форматы кандидат готов рассматривать: office, hybrid, remote.
- salary_expectation: желаемая зарплата на руки в рублях в месяц, целое число. Если в резюме
  сумма до вычета налогов, умножь её на 0,87.
- stack: технологии, языки, фреймворки и инструменты в общепринятом написании (Python,
  PostgreSQL, Docker), без версий и повторов, до 30, каждая короче 40 символов.
- soft_skills: личные качества, если они явно названы, по-русски, до 10.
- about: 2–3 предложения о себе от первого лица по фактам резюме, до 600 символов.
Контакты в тексте заменены на {HIDDEN}, не восстанавливай их."""

_TEXT: Final[dict[str, Any]] = {"type": ["string", "null"]}
_LIST: Final[dict[str, Any]] = {"type": "array", "items": {"type": "string"}}
SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "display_name": _TEXT,
        "headline": _TEXT,
        "specialization": {"type": ["string", "null"], "enum": [*SPECIALIZATIONS, None]},
        "experience_years": {"type": ["integer", "null"]},
        "city": _TEXT,
        "work_formats": {
            "type": "array",
            "items": {"type": "string", "enum": [item.value for item in WorkFormat]},
        },
        "salary_expectation": {"type": ["integer", "null"]},
        "stack": _LIST,
        "soft_skills": _LIST,
        "about": _TEXT,
    },
}
# Strict structured outputs require every property to be listed.
SCHEMA["required"] = list(SCHEMA["properties"])


class ResumeReaderUnavailableError(ServiceUnavailableError):
    code = "resume_reader_unavailable"
    default_message = "Распознавание резюме сейчас недоступно. Заполните поля вручную."


class ResumeReader(Protocol):
    async def read(self, text: str) -> dict[str, Any]:
        """Raw fields as the model returned them; the caller validates every value."""
        ...


class LlmResumeReader:
    def __init__(self, model: JsonModel) -> None:
        self._model = model

    async def read(self, text: str) -> dict[str, Any]:
        try:
            return await self._model.ask(
                system=INSTRUCTIONS, user=text, schema=SCHEMA, max_tokens=_MAX_TOKENS
            )
        except LlmUnavailableError as exc:
            raise ResumeReaderUnavailableError() from exc
