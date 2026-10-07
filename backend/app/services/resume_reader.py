"""Reads resume fields with a language model on RouterAI (https://routerai.ru/docs).

Plug-in point: set `ROUTERAI_API_KEY`; `RESUME_PARSER_MODEL` picks the model. The key stays on
the server. Swap the provider by implementing `ResumeReader`.
"""

import asyncio
import json
import logging
import urllib.error
import urllib.request
from typing import Any, Final, Protocol

from app.core.config import Settings
from app.core.errors import ServiceUnavailableError
from app.models.enums import WorkFormat
from app.services.categories import SPECIALIZATIONS
from app.services.resume_text import HIDDEN

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT: Final = 60
_MAX_PARALLEL: Final = 4
# The JSON answer is under 1 000 tokens; the rest is room for the model's reasoning.
_MAX_TOKENS: Final = 4000
_slots = asyncio.Semaphore(_MAX_PARALLEL)

_SPECIALIZATION_LIST = "; ".join(f"{code} — {label}" for code, label in SPECIALIZATIONS.items())

INSTRUCTIONS: Final = f"""Ты переносишь резюме ИТ-специалиста в анкету платформы подбора.
Верни только JSON по схеме. Чего нет в резюме — null или пустой список, ничего не придумывай.
- display_name: имя и фамилия, как в резюме.
- headline: желаемая должность или текущая роль, коротко, например «Python-разработчик».
- specialization: код ближайшей специализации по основной роли: {_SPECIALIZATION_LIST}.
- experience_years: полных лет опыта работы в ИТ (сумма периодов работы, без учёбы).
- city: город проживания по-русски, без страны.
- work_formats: какие форматы кандидат готов рассматривать: office, hybrid, remote.
- salary_expectation: желаемая зарплата в рублях в месяц, целое число, как в резюме (на руки или
  до вычета налогов — не пересчитывай).
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


class RouterAiResumeReader:
    def __init__(self, settings: Settings) -> None:
        self._key = settings.routerai_api_key.get_secret_value().strip()
        self._url = settings.routerai_url.rstrip("/") + "/chat/completions"
        self._model = settings.resume_parser_model
        self._reasoning = settings.resume_parser_reasoning.strip()

    async def read(self, text: str) -> dict[str, Any]:
        if not self._key:
            raise ResumeReaderUnavailableError()
        async with _slots:
            try:
                body = await asyncio.to_thread(_post, self._url, self._key, self._payload(text))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:300]
                logger.error("RouterAI rejected the resume request (%s): %s", exc.code, detail)
                raise ResumeReaderUnavailableError() from exc
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                logger.error("RouterAI is unreachable: %s", exc)
                raise ResumeReaderUnavailableError() from exc
        usage = body.get("usage") or {}
        logger.info(
            "Resume read by %s: %s tokens, %s RUB",
            self._model,
            usage.get("total_tokens"),
            usage.get("cost"),
        )
        return _answer(body)

    def _payload(self, text: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": INSTRUCTIONS},
                {"role": "user", "content": text},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "resume", "strict": True, "schema": SCHEMA},
            },
            "max_tokens": _MAX_TOKENS,
        }
        if self._reasoning:
            payload["reasoning"] = {"effort": self._reasoning}
        return payload


def _answer(body: dict[str, Any]) -> dict[str, Any]:
    """The JSON object of the reply; a code fence or a phrase around it is tolerated."""
    try:
        content = str(body["choices"][0]["message"]["content"] or "")
    except (KeyError, IndexError, TypeError) as exc:
        raise ResumeReaderUnavailableError() from exc
    start, end = content.find("{"), content.rfind("}")
    try:
        parsed = json.loads(content[start : end + 1]) if start != -1 else None
    except json.JSONDecodeError:
        parsed = None
    if not isinstance(parsed, dict):
        logger.error("The resume model answered without a JSON object: %.200s", content)
        raise ResumeReaderUnavailableError()
    return parsed


def _post(url: str, api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(  # noqa: S310 - fixed https endpoint from settings
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT) as response:  # noqa: S310
        parsed = json.loads(response.read().decode("utf-8"))
    if not isinstance(parsed, dict):
        raise json.JSONDecodeError("expected an object", "", 0)
    return parsed
