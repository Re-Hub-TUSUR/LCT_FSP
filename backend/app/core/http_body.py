"""Bodies of the external services we call: read up to a limit, never whole whatever comes."""

import json
from typing import Any, Final, Protocol

# Far above any real answer of the compiler, the model or the FSP registry.
MAX_RESPONSE_BYTES: Final = 2 * 1024 * 1024


class _Readable(Protocol):
    def read(self, amt: int, /) -> bytes: ...


def read_json(response: _Readable, limit: int = MAX_RESPONSE_BYTES) -> Any:
    """A broken or hostile upstream could stream gigabytes into memory otherwise.

    An oversized body is reported as undecodable JSON: every caller already treats that as
    «the service is unavailable».
    """
    body = response.read(limit + 1)
    if len(body) > limit:
        msg = f"response is larger than {limit} bytes"
        raise json.JSONDecodeError(msg, "", 0)
    return json.loads(body.decode("utf-8"))
