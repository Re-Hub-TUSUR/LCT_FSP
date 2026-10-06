import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, ClassVar

import pytest

from app.core.config import Settings
from app.services.code_runner import CodeRunnerUnavailableError, OnlineCompilerRunner

KEY = "test-key"


class FakeCompiler(BaseHTTPRequestHandler):
    """Answers like POST /api/run-code-sync/ of onlinecompiler.io."""

    requests: ClassVar[list[dict[str, Any]]] = []
    # Status codes to answer before the first success.
    failures: ClassVar[list[int]] = []

    def do_POST(self) -> None:
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).requests.append({"auth": self.headers["Authorization"], **body})
        if type(self).failures:
            self.send_response(type(self).failures.pop(0))
            self.end_headers()
            return
        crashed = "raise" in body["code"]
        payload = {
            "output": "" if crashed else body["input"].upper(),
            "error": "Traceback (most recent call last)" if crashed else "",
            "status": "error" if crashed else "success",
            "exit_code": 1 if crashed else 0,
            "signal": None,
            "time": 0.012,
            "total": 0.3,
            "memory": 9000,
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def log_message(self, *_: object) -> None:
        """Keeps the test output quiet."""


@pytest.fixture
def compiler() -> Iterator[str]:
    FakeCompiler.requests.clear()
    FakeCompiler.failures.clear()
    server = HTTPServer(("127.0.0.1", 0), FakeCompiler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join()


def runner(url: str, key: str = KEY) -> OnlineCompilerRunner:
    return OnlineCompilerRunner(Settings(onlinecompiler_api_key=key, onlinecompiler_url=url))


async def test_run_sends_the_documented_request(compiler: str) -> None:
    result = await runner(compiler).run(compiler="python-3.14", code="print()", stdin="abc")

    assert (result.ok, result.output, result.time, result.killed) == (True, "ABC", 0.012, False)
    assert FakeCompiler.requests == [
        {"auth": KEY, "compiler": "python-3.14", "code": "print()", "input": "abc"}
    ]


async def test_failed_program_is_not_ok(compiler: str) -> None:
    result = await runner(compiler).run(compiler="python-3.14", code="raise X", stdin="")

    assert result.ok is False
    assert result.error.startswith("Traceback")


async def test_rate_limit_is_retried(compiler: str, monkeypatch: pytest.MonkeyPatch) -> None:
    async def no_wait(_: float) -> None:
        return None

    monkeypatch.setattr("app.services.code_runner.asyncio.sleep", no_wait)
    FakeCompiler.failures.append(429)

    result = await runner(compiler).run(compiler="python-3.14", code="print()", stdin="x")

    assert result.output == "X"
    assert len(FakeCompiler.requests) == 2


async def test_service_error_is_reported_as_unavailable(compiler: str) -> None:
    FakeCompiler.failures.append(500)

    with pytest.raises(CodeRunnerUnavailableError):
        await runner(compiler).run(compiler="python-3.14", code="print()", stdin="x")


async def test_without_a_key_nothing_is_sent(compiler: str) -> None:
    keyless = runner(compiler, key="")

    assert keyless.available is False
    with pytest.raises(CodeRunnerUnavailableError):
        await keyless.run(compiler="python-3.14", code="print()", stdin="x")
    assert FakeCompiler.requests == []
