"""Runs candidate code on onlinecompiler.io (https://onlinecompiler.io/docs).

Plug-in point: set `ONLINECOMPILER_API_KEY`. The key stays on the server — hidden tests would
leak if the browser talked to the compiler itself. Swap the provider by implementing `CodeRunner`.
"""

import asyncio
import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Final, Protocol

from app.core.config import Settings
from app.core.errors import AppError
from app.core.http_body import read_json

logger = logging.getLogger(__name__)

# Compiler ids of GET /api/compilers/.
COMPILERS: Final[dict[str, str]] = {
    "python-3.14": "Python 3.14",
    "typescript-deno": "TypeScript (Deno)",
    "openjdk-25": "Java 25",
    "g++-15": "C++ (G++ 15)",
    "gcc-15": "C (GCC 15)",
    "dotnet-csharp-9": "C# (.NET 9)",
    "go-1.26": "Go 1.26",
    "rust-1.93": "Rust 1.93",
    "php-8.5": "PHP 8.5",
    "ruby-4.0": "Ruby 4.0",
    "haskell-9.12": "Haskell (GHC 9.12)",
    "dotnet-fsharp-9": "F# (.NET 9)",
}

# The service allows 4 synchronous runs at once and answers 429 beyond that.
_MAX_PARALLEL: Final = 3
_RETRIES: Final = 3
_HTTP_TIMEOUT: Final = 35
_HTTP_TOO_MANY_REQUESTS: Final = 429
_slots = asyncio.Semaphore(_MAX_PARALLEL)


class CodeRunnerUnavailableError(AppError):
    status_code = 503
    code = "code_runner_unavailable"
    default_message = "Проверка кода временно недоступна. Попробуйте позже."


@dataclass(frozen=True, slots=True)
class Execution:
    """Outcome of one program run."""

    ok: bool
    output: str
    error: str
    # Seconds of execution without compilation; None when the program did not start.
    time: float | None
    killed: bool = False


class CodeRunner(Protocol):
    @property
    def available(self) -> bool: ...

    async def run(self, *, compiler: str, code: str, stdin: str) -> Execution: ...


class OnlineCompilerRunner:
    def __init__(self, settings: Settings) -> None:
        self._key = settings.onlinecompiler_api_key.get_secret_value().strip()
        self._url = settings.onlinecompiler_url.rstrip("/") + "/api/run-code-sync/"

    @property
    def available(self) -> bool:
        return bool(self._key)

    async def run(self, *, compiler: str, code: str, stdin: str) -> Execution:
        if not self._key:
            raise CodeRunnerUnavailableError("ONLINECOMPILER_API_KEY не задан")
        payload = {"compiler": compiler, "code": code, "input": stdin}
        async with _slots:
            for attempt in range(_RETRIES):
                try:
                    body = await asyncio.to_thread(_post, self._url, self._key, payload)
                except urllib.error.HTTPError as exc:
                    if exc.code == _HTTP_TOO_MANY_REQUESTS and attempt + 1 < _RETRIES:
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                    detail = exc.read().decode("utf-8", errors="replace")[:300]
                    logger.error("Code runner rejected the run (%s): %s", exc.code, detail)
                    raise CodeRunnerUnavailableError() from exc
                except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                    logger.error("Code runner is unreachable: %s", exc)
                    raise CodeRunnerUnavailableError() from exc
                return _execution(body)
        raise CodeRunnerUnavailableError()  # pragma: no cover - the loop always returns or raises


def _execution(body: dict[str, Any]) -> Execution:
    exit_code = body.get("exit_code")
    signal = body.get("signal")
    time = body.get("time")
    return Execution(
        ok=body.get("status") == "success" and exit_code in (0, None) and signal is None,
        output=str(body.get("output") or ""),
        error=str(body.get("error") or ""),
        time=float(time) if isinstance(time, int | float) else None,
        killed=signal is not None,
    )


def _post(url: str, api_key: str, payload: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(  # noqa: S310 - fixed https endpoint from settings
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT) as response:  # noqa: S310
        parsed = read_json(response)
    if not isinstance(parsed, dict):
        raise json.JSONDecodeError("expected an object", "", 0)
    return parsed
