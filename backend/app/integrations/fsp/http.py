"""Blocking JSON-over-HTTP calls, run in a thread so the event loop stays free."""

import asyncio
import json
import urllib.error
import urllib.request
from typing import Any, Final
from urllib.parse import urlencode

TIMEOUT: Final = 10


class HttpCallError(Exception):
    """Transport failure or an error status; `status` is None when no answer came."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


async def post_form(url: str, form: dict[str, str]) -> dict[str, Any]:
    return await asyncio.to_thread(
        _call,
        url,
        data=urlencode(form).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


async def get_json(url: str, *, bearer: str) -> dict[str, Any]:
    return await asyncio.to_thread(
        _call, url, data=None, headers={"Authorization": f"Bearer {bearer}"}
    )


def _call(url: str, *, data: bytes | None, headers: dict[str, str]) -> dict[str, Any]:
    if not url.startswith(("https://", "http://")):
        msg = f"not an absolute URL: {url}"
        raise HttpCallError(msg)
    request = urllib.request.Request(  # noqa: S310 - the scheme is checked above
        url,
        data=data,
        headers={"Accept": "application/json", **headers},
        method="POST" if data is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:  # noqa: S310
            parsed = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise HttpCallError(f"HTTP {exc.code}", exc.code) from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HttpCallError(str(exc)) from exc
    if not isinstance(parsed, dict):
        msg = "expected a JSON object"
        raise HttpCallError(msg)
    return parsed
