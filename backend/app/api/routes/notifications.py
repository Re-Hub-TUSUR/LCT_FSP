import asyncio
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from starlette.responses import StreamingResponse

from app.core.errors import TooManyRequestsError
from app.dependencies.auth import CurrentUser
from app.services.notifications import NotificationHub, TooManyStreamsError

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/stream", summary="Live updates for likes and chat")
async def stream(user: CurrentUser, request: Request) -> StreamingResponse:
    hub: NotificationHub = request.app.state.notifications
    try:
        queue = hub.subscribe(user.id)
    except TooManyStreamsError as exc:
        raise TooManyRequestsError("Слишком много открытых вкладок с уведомлениями") from exc

    async def events() -> AsyncIterator[str]:
        try:
            yield "event: ready\ndata: {}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=25.0)
                except TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                yield f"data: {payload}\n\n"
        finally:
            hub.unsubscribe(user.id, queue)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
