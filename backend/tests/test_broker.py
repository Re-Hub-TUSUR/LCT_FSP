"""A channel is one user's, never another's — the guarantee `NotificationHub` relies on.

The Redis-backed broker is exercised against a real server only:
`TEST_REDIS_URL=redis://localhost:6379/0 uv run pytest tests/test_broker.py`.

That one test is occasionally slow to see its own message come back when run inside this
specific suite (CPython's asyncio pub/sub delivery over Windows sometimes lags behind many other
async tests sharing one event loop) — a rerun passes. A script that runs `RedisBroker` alone,
the way `app/main.py` actually does for the life of a whole process, sees none of this.
"""

import asyncio
import os
import uuid

import pytest

from app.services.broker import InProcessBroker, RedisBroker, user_channel
from app.services.notifications import NotificationHub

REDIS_URL = os.environ.get("TEST_REDIS_URL", "")


def test_user_channel_never_collides() -> None:
    a, b = uuid.uuid4(), uuid.uuid4()
    assert user_channel(a) != user_channel(b)
    assert user_channel(a) == user_channel(a)


async def test_in_process_broker_keeps_channels_apart() -> None:
    broker = InProcessBroker()
    mine: asyncio.Queue[str] = asyncio.Queue()
    theirs: asyncio.Queue[str] = asyncio.Queue()
    broker.subscribe("user:me", mine)
    broker.subscribe("user:them", theirs)

    await broker.publish("user:me", "for me only")

    assert mine.get_nowait() == "for me only"
    assert theirs.empty()


async def test_in_process_broker_reaches_every_subscriber_of_one_channel() -> None:
    broker = InProcessBroker()
    tab1: asyncio.Queue[str] = asyncio.Queue()
    tab2: asyncio.Queue[str] = asyncio.Queue()
    broker.subscribe("user:me", tab1)
    broker.subscribe("user:me", tab2)

    await broker.publish("user:me", "to both tabs")

    assert tab1.get_nowait() == "to both tabs"
    assert tab2.get_nowait() == "to both tabs"


async def test_in_process_broker_forgets_a_channel_once_empty() -> None:
    broker = InProcessBroker()
    queue: asyncio.Queue[str] = asyncio.Queue()
    broker.subscribe("user:me", queue)
    broker.unsubscribe("user:me", queue)

    # No subscriber left: publishing is a no-op, not an error on a channel nobody owns any more.
    await broker.publish("user:me", "too late")
    assert queue.empty()


async def test_hub_never_lets_one_account_see_another_accounts_events() -> None:
    hub = NotificationHub(InProcessBroker())
    me, them = uuid.uuid4(), uuid.uuid4()
    mine = hub.subscribe(me)
    theirs = hub.subscribe(them)

    await hub.publish(me, {"type": "message", "text": "for me"})

    assert await asyncio.wait_for(mine.get(), timeout=1) == '{"type": "message", "text": "for me"}'
    assert theirs.empty()


@pytest.mark.skipif(not REDIS_URL, reason="TEST_REDIS_URL is not set")
async def test_redis_broker_round_trips_through_a_real_server() -> None:
    broker = RedisBroker(REDIS_URL)
    try:
        me, them = uuid.uuid4(), uuid.uuid4()
        mine: asyncio.Queue[str] = asyncio.Queue()
        theirs: asyncio.Queue[str] = asyncio.Queue()
        broker.subscribe(user_channel(me), mine)
        broker.subscribe(user_channel(them), theirs)
        # The SUBSCRIBE is sent in the background (see `RedisBroker.subscribe`); one plain wait
        # for it to land, not a poll loop — a timer created and cancelled on every spin is its
        # own source of jitter on a test runner's shared event loop.
        await asyncio.sleep(0.3)

        await broker.publish(user_channel(me), "hello")

        assert await asyncio.wait_for(mine.get(), timeout=5) == "hello"
        assert theirs.empty()
    finally:
        await broker.close()
