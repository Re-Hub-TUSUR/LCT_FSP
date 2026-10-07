"""Chat completions on RouterAI (https://routerai.ru/docs) that answer with one JSON object.

Only Russian models are allowed, i.e. the Yandex family. They accept `response_format` with a
JSON schema but reject `reasoning`, so it is never sent. The key stays on the server.
"""

import asyncio
import json
import logging
import urllib.error
import urllib.request
from typing import Any, Final, Protocol

from app.core.config import Settings
from app.core.errors import ServiceUnavailableError

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT: Final = 60
_MAX_PARALLEL: Final = 4
_slots = asyncio.Semaphore(_MAX_PARALLEL)


class LlmUnavailableError(ServiceUnavailableError):
    code = "llm_unavailable"
    default_message = "Нейросеть сейчас недоступна. Попробуйте позже."


class JsonModel(Protocol):
    @property
    def available(self) -> bool: ...

    async def ask(
        self, *, system: str, user: str, schema: dict[str, Any], max_tokens: int
    ) -> dict[str, Any]:
        """The JSON object the model answered with; the caller validates every value."""
        ...


class RouterAiModel:
    def __init__(self, settings: Settings, model: str) -> None:
        self._key = settings.routerai_api_key.get_secret_value().strip()
        self._url = settings.routerai_url.rstrip("/") + "/chat/completions"
        self._model = model

    @property
    def available(self) -> bool:
        return bool(self._key)

    async def ask(
        self, *, system: str, user: str, schema: dict[str, Any], max_tokens: int
    ) -> dict[str, Any]:
        if not self._key:
            raise LlmUnavailableError("ROUTERAI_API_KEY не задан")
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "answer", "strict": True, "schema": schema},
            },
            "max_tokens": max_tokens,
        }
        async with _slots:
            try:
                body = await asyncio.to_thread(_post, self._url, self._key, payload)
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:300]
                logger.error("RouterAI rejected the request (%s): %s", exc.code, detail)
                raise LlmUnavailableError() from exc
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                logger.error("RouterAI is unreachable: %s", exc)
                raise LlmUnavailableError() from exc
        usage = body.get("usage") or {}
        logger.info(
            "%s answered: %s tokens, %s RUB",
            self._model,
            usage.get("total_tokens"),
            usage.get("cost"),
        )
        return _answer(body)


def _answer(body: dict[str, Any]) -> dict[str, Any]:
    """The JSON object of the reply; a code fence or a phrase around it is tolerated."""
    # A provider error comes back with HTTP 200 and an `error` object instead of `choices`.
    if "error" in body:
        logger.error("RouterAI returned an error: %.300s", json.dumps(body["error"]))
        raise LlmUnavailableError()
    try:
        content = str(body["choices"][0]["message"]["content"] or "")
    except (KeyError, IndexError, TypeError) as exc:
        raise LlmUnavailableError() from exc
    start, end = content.find("{"), content.rfind("}")
    try:
        parsed = json.loads(content[start : end + 1]) if start != -1 else None
    except json.JSONDecodeError:
        parsed = None
    if not isinstance(parsed, dict):
        logger.error("The model answered without a JSON object: %.200s", content)
        raise LlmUnavailableError()
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
