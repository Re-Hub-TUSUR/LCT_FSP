"""SSE fan-out, addressed one user at a time: see `app.services.broker` for how that is kept true
even once there is more than one backend worker to publish from or subscribe through."""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any

from app.services.broker import Broker, InProcessBroker, user_channel

logger = logging.getLogger(__name__)


# Tabs and devices of one person; every stream holds a connection and a queue.
MAX_STREAMS_PER_USER = 8


class TooManyStreamsError(Exception):
    pass


class NotificationHub:
    """Each person's events travel on their own broker channel (`user_channel`), so a message is
    structurally addressed to one recipient and cannot drift to another's queue."""

    def __init__(self, broker: Broker | None = None) -> None:
        self._broker = broker or InProcessBroker()
        # The per-account stream cap is local to this worker: it bounds one person's open tabs,
        # not a count the broker needs to agree on across a fleet.
        self._counts: dict[uuid.UUID, int] = defaultdict(int)

    def subscribe(self, user_id: uuid.UUID) -> asyncio.Queue[str]:
        if self._counts[user_id] >= MAX_STREAMS_PER_USER:
            raise TooManyStreamsError
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=64)
        self._broker.subscribe(user_channel(user_id), queue)
        self._counts[user_id] += 1
        return queue

    def unsubscribe(self, user_id: uuid.UUID, queue: asyncio.Queue[str]) -> None:
        self._broker.unsubscribe(user_channel(user_id), queue)
        self._counts[user_id] -= 1
        if self._counts[user_id] <= 0:
            del self._counts[user_id]

    async def publish(self, user_id: uuid.UUID, event: dict[str, Any]) -> None:
        payload = json.dumps(event, ensure_ascii=False)
        await self._broker.publish(user_channel(user_id), payload)

    async def close(self) -> None:
        await self._broker.close()


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
