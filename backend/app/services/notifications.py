"""In-process SSE fan-out for the current uvicorn worker."""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class NotificationHub:
    def __init__(self) -> None:
        self._queues: dict[uuid.UUID, set[asyncio.Queue[str]]] = defaultdict(set)

    def subscribe(self, user_id: uuid.UUID) -> asyncio.Queue[str]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=64)
        self._queues[user_id].add(queue)
        return queue

    def unsubscribe(self, user_id: uuid.UUID, queue: asyncio.Queue[str]) -> None:
        self._queues[user_id].discard(queue)
        if not self._queues[user_id]:
            del self._queues[user_id]

    async def publish(self, user_id: uuid.UUID, event: dict[str, Any]) -> None:
        payload = json.dumps(event, ensure_ascii=False)
        stale: list[asyncio.Queue[str]] = []
        for queue in self._queues.get(user_id, ()):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                stale.append(queue)
        for queue in stale:
            self._queues[user_id].discard(queue)
        if stale:
            logger.warning("Dropped %s slow SSE subscriber(s) for user %s", len(stale), user_id)


async def announce_meeting(
    hub: NotificationHub | None,
    *,
    user_id: uuid.UUID,
    meeting_id: uuid.UUID,
    company_name: str,
    title: str,
    starts_at: datetime,
) -> None:
    """Tells the candidate that a meeting waits for their answer."""
    if hub is None:
        return
    await hub.publish(
        user_id,
        {
            "type": "meeting_pending",
            "meetingId": str(meeting_id),
            "companyName": company_name,
            "title": title,
            "startsAt": starts_at.isoformat(),
        },
    )
