from collections.abc import Awaitable, Callable

from fastapi import Request, Response

# JSON must not be sniffed and rendered as HTML, and the API must not be framed.
_API_CSP = "default-src 'none'; frame-ancestors 'none'"


async def security_headers_middleware(
    _request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(_request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    # The only HTML pages (the emulated FSP ID sign-in) set a narrower policy of their own.
    response.headers.setdefault("Content-Security-Policy", _API_CSP)
    return response
