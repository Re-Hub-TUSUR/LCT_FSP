"""Pub/sub broker behind the notification hub: a channel belongs to one user, and only to them.

`InProcessBroker` is the default — an in-memory fan-out, scoped per channel name, that works
alone on one worker. It is what `NotificationHub` has always used; this module only gives that
logic a name and an interface, so the invariant ("a channel is one user's, never mixed with
another's") is explicit and has its own test instead of living implicitly inside the hub.

The gap it does not close by itself: publish and subscribe must run in the *same* worker process.
Scaled to several (more uvicorn workers, more replicas behind a load balancer), a message
published on one worker never reaches a subscriber connected to another — not a wrong-recipient
bug, but a dropped one. `RedisBroker` closes that gap: every worker subscribes to the same named
channels over Redis pub/sub, so a `kadry:user:<id>` channel still reaches only its one user,
wherever in the fleet they are connected and wherever the message was published from. Point
`BROKER_URL` at Redis to switch; no caller of `NotificationHub` changes.
"""

from __future__ import annotations

import abc
import asyncio
import contextlib
import logging
import uuid
from collections import defaultdict
from collections.abc import Awaitable

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


def user_channel(user_id: uuid.UUID) -> str:
    """The one channel a user's own messages are published and subscribed under."""
    return f"kadry:user:{user_id}"


class Broker(abc.ABC):
    """Keeps channels apart; addressing which channel is a user's is the caller's job (see
    `user_channel`). `subscribe`/`unsubscribe` are synchronous — a websocket-style route hands
    over a queue it already owns and must keep working with it immediately, before any I/O."""

    @abc.abstractmethod
    def subscribe(self, channel: str, queue: asyncio.Queue[str]) -> None:
        """From now on, whatever is published to `channel` is put on `queue`, until unsubscribed."""

    @abc.abstractmethod
    def unsubscribe(self, channel: str, queue: asyncio.Queue[str]) -> None:
        """No-op if `queue` was not subscribed to `channel` (a route's cleanup may run twice)."""

    @abc.abstractmethod
    async def publish(self, channel: str, payload: str) -> None:
        """Delivers `payload` to every queue currently subscribed to `channel`, if any."""

    async def close(self) -> None:  # noqa: B027 - a default no-op; InProcessBroker needs no cleanup
        """Releases connections or tasks the broker opened. The in-process one needs none."""


class InProcessBroker(Broker):
    """Every queue lives in this worker's memory. Fine alone; add `RedisBroker` once more than
    one worker or replica is deployed, so a publish on one reaches a subscriber on another."""

    def __init__(self) -> None:
        self._queues: dict[str, set[asyncio.Queue[str]]] = defaultdict(set)

    def subscribe(self, channel: str, queue: asyncio.Queue[str]) -> None:
        self._queues[channel].add(queue)

    def unsubscribe(self, channel: str, queue: asyncio.Queue[str]) -> None:
        self._queues[channel].discard(queue)
        if not self._queues[channel]:
            del self._queues[channel]

    async def publish(self, channel: str, payload: str) -> None:
        stale: list[asyncio.Queue[str]] = []
        for queue in self._queues.get(channel, ()):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                stale.append(queue)
        for queue in stale:
            self._queues[channel].discard(queue)
        if stale:
            logger.warning("Dropped %d slow subscriber(s) of %s", len(stale), channel)


class RedisBroker(Broker):
    """Pub/sub over Redis (`redis.asyncio`). One connection subscribes to every channel this
    worker has a local listener for; one background task reads it and fans each message out to
    the local queues `subscribe` was given — callers never see Redis itself."""

    def __init__(self, url: str) -> None:
        self._redis: Redis = Redis.from_url(url)
        self._pubsub = self._redis.pubsub(ignore_subscribe_messages=True)
        self._queues: dict[str, set[asyncio.Queue[str]]] = defaultdict(set)
        self._reader: asyncio.Task[None] | None = None
        # Holds the SUBSCRIBE/UNSUBSCRIBE commands `subscribe`/`unsubscribe` start in the
        # background: with nothing else referencing them, a task can be garbage-collected before
        # the event loop ever runs it, and the command would silently never reach Redis.
        self._pending: set[asyncio.Task[object]] = set()

    def _spawn(self, awaitable: Awaitable[object]) -> None:
        task = asyncio.ensure_future(awaitable)
        self._pending.add(task)
        task.add_done_callback(self._pending.discard)

    def subscribe(self, channel: str, queue: asyncio.Queue[str]) -> None:
        first = channel not in self._queues
        self._queues[channel].add(queue)
        if first:
            # Sent in the background: the SUBSCRIBE reaches Redis over the one connection in the
            # order it was scheduled, so two calls from this worker never race each other. A
            # publish from elsewhere landing in the same instant as the very first subscriber is
            # the ordinary pub/sub gap (no history), not something specific to this broker.
            self._spawn(self._subscribe_then_read(channel))

    async def _subscribe_then_read(self, channel: str) -> None:
        await self._pubsub.subscribe(channel)
        # Started only once something is actually subscribed: `listen()` reads
        # `pubsub.subscribed` and, called before the SUBSCRIBE above lands, stops at once rather
        # than waiting for a subscription that is still on its way.
        if self._reader is None:
            self._reader = asyncio.create_task(self._read())

    def unsubscribe(self, channel: str, queue: asyncio.Queue[str]) -> None:
        if channel not in self._queues:
            return
        self._queues[channel].discard(queue)
        if not self._queues[channel]:
            del self._queues[channel]
            self._spawn(self._pubsub.unsubscribe(channel))

    async def publish(self, channel: str, payload: str) -> None:
        await self._redis.publish(channel, payload)

    async def _read(self) -> None:
        with contextlib.suppress(asyncio.CancelledError):
            async for message in self._pubsub.listen():
                if message["type"] != "message":
                    continue
                channel = _text(message["channel"])
                payload = _text(message["data"])
                for queue in self._queues.get(channel, ()):
                    with contextlib.suppress(asyncio.QueueFull):
                        queue.put_nowait(payload)

    async def close(self) -> None:
        if self._pending:
            await asyncio.gather(*self._pending, return_exceptions=True)
        if self._reader is not None:
            self._reader.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reader
        await self._pubsub.aclose()  # type: ignore[no-untyped-call]  # redis-py's stub is incomplete
        await self._redis.aclose()


def _text(value: bytes | str) -> str:
    return value.decode() if isinstance(value, bytes) else value
