"""Shares, medians and flags of the admin analytics."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import Float, literal, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.admin.analytics.metrics import (
    FlagRules,
    TaskFlag,
    invites_anomalous,
    outcome_shares,
    response_low,
    share,
    task_flags,
)
from app.admin.analytics.sql import Dialect, medians
from app.admin.dictionaries import DEFAULTS
from app.core.security import hash_password
from app.models import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentTaskTime,
    AttemptStatus,
    CandidateProfile,
    Grade,
    User,
    UserRole,
)
from tests.conftest import API, PASSWORD, bearer, create_admin, login

RULES = FlagRules.from_parameters(DEFAULTS)

# ── Pure rules ──────────────────────────────────────────────────────────────────────────────────


def test_share_rounds_and_handles_zero() -> None:
    assert share(1, 3) == 33.3
    assert share(0, 0) is None
    assert share(None, 10) == 0.0


def test_outcome_shares_sum_to_hundred() -> None:
    result = outcome_shares(attempts=40, full=10, partial=6, abandoned=4)
    assert result == {
        "attempts": 40,
        "fullShare": 25.0,
        "partialShare": 15.0,
        "abandonedShare": 10.0,
        "unsolvedShare": 50.0,
    }


def test_no_flags_below_minimum_attempts() -> None:
    flags = task_flags(
        RULES, attempts=29, full_share=5.0, variant_spread_pp=50.0, max_weekly_jump_pp=50.0
    )
    assert flags == []


@pytest.mark.parametrize(
    ("full_share", "flagged"),
    [(49.9, True), (50.0, False), (60.0, False), (70.0, False), (70.1, True)],
)
def test_target_difficulty_bounds(full_share: float, flagged: bool) -> None:
    flags = task_flags(
        RULES, attempts=30, full_share=full_share, variant_spread_pp=None, max_weekly_jump_pp=None
    )
    assert (TaskFlag.OUT_OF_TARGET in flags) is flagged


def test_spread_and_leak_are_strictly_above_thresholds() -> None:
    at_threshold = task_flags(
        RULES, attempts=100, full_share=60.0, variant_spread_pp=10.0, max_weekly_jump_pp=20.0
    )
    above = task_flags(
        RULES, attempts=100, full_share=60.0, variant_spread_pp=10.1, max_weekly_jump_pp=20.1
    )
    assert at_threshold == []
    assert above == [TaskFlag.VARIANT_SPREAD, TaskFlag.POSSIBLE_LEAK]


def test_flags_follow_changed_parameters() -> None:
    rules = FlagRules.from_parameters({**DEFAULTS, "min_attempts_for_flags": 5, "leak_jump_pp": 50})
    flags = task_flags(
        rules, attempts=5, full_share=60.0, variant_spread_pp=None, max_weekly_jump_pp=30.0
    )
    assert flags == []


def test_invite_anomaly() -> None:
    assert invites_anomalous(31, 10.0, factor=3, minimum=10)
    assert not invites_anomalous(30, 10.0, factor=3, minimum=10)
    assert not invites_anomalous(9, 1.0, factor=3, minimum=10)
    assert not invites_anomalous(50, None, factor=3, minimum=10)


def test_low_response() -> None:
    assert response_low(inbound=10, responded=1, threshold=20, minimum=10)
    assert not response_low(inbound=10, responded=2, threshold=20, minimum=10)
    assert not response_low(inbound=9, responded=0, threshold=20, minimum=10)


# ── Median in the database ──────────────────────────────────────────────────────────────────────


async def test_median_odd_even_and_nulls(sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    values = [("a", 1.0), ("a", 3.0), ("a", 2.0), ("b", 4.0), ("b", 1.0), ("b", None), ("c", None)]
    rows = union_all(
        *(
            select(literal(group).label("grp"), literal(value, Float).label("value"))
            for group, value in values
        )
    ).subquery()
    async with sessionmaker() as session:
        result = await medians(session, Dialect.of(session), rows, "value", ["grp"])
        whole = await medians(session, Dialect.of(session), rows, "value", [])
    assert result == {("a",): 2.0, ("b",): 2.5}
    assert whole == {(): 2.0}


# ── Task analytics end to end ───────────────────────────────────────────────────────────────────


async def _candidate(sessionmaker: async_sessionmaker[AsyncSession]) -> uuid.UUID:
    async with sessionmaker() as session:
        user = User(
            email=f"{uuid.uuid4().hex[:8]}@fsp.ru",
            password_hash=hash_password(PASSWORD),
            role=UserRole.CANDIDATE,
            is_email_verified=True,
        )
        session.add(user)
        await session.flush()
        profile = CandidateProfile(user_id=user.id, display_name="Тест")
        session.add(profile)
        await session.commit()
        return profile.id


async def _attempts(
    sessionmaker: async_sessionmaker[AsyncSession],
    candidate_id: uuid.UUID,
    task_id: str,
    *,
    started: datetime,
    minutes: int,
    variant: str,
    grade: Grade,
    points: Sequence[float | None],
    expired: int = 0,
) -> None:
    """One attempt per item of `points` (None = no answer sent) plus `expired` abandoned ones."""
    async with sessionmaker() as session:
        for index, value in enumerate([*points, *([None] * expired)]):
            is_expired = index >= len(points)
            start = started + timedelta(minutes=index)
            attempt = AssessmentAttempt(
                candidate_id=candidate_id,
                title="Тест",
                specialization="backend",
                grade=grade,
                status=AttemptStatus.EXPIRED if is_expired else AttemptStatus.FAILED,
                pass_score=60,
                quiz_weight=40,
                started_at=start,
                expires_at=start + timedelta(minutes=60),
                finished_at=start + timedelta(minutes=60 if is_expired else minutes),
                task_ids=[task_id],
                tasks=[],
                task_state={task_id: {"variant": variant}},
            )
            session.add(attempt)
            await session.flush()
            if not is_expired:
                # The runner reports the time the task was on screen.
                session.add(
                    AssessmentTaskTime(
                        attempt_id=attempt.id, task_id=uuid.UUID(task_id), seconds=minutes * 60
                    )
                )
            if value is not None:
                session.add(
                    AssessmentAnswer(
                        attempt_id=attempt.id,
                        task_id=uuid.UUID(task_id),
                        answer={"selected": [0]},
                        points=value,
                    )
                )
        await session.commit()


def quiz_task(title: str) -> dict[str, Any]:
    return {
        "kind": "quiz",
        "title": title,
        "statement": "Сколько будет {a} + {b}?",
        "specializations": ["backend"],
        "grade": "junior",
        "skill": "arithmetic",
        "variables": [{"name": "a", "min": 1, "max": 9}, {"name": "b", "min": 1, "max": 9}],
        "payload": {"options": ["верно", "неверно"], "correct": [0]},
        "status": "active",
    }


@pytest.fixture
async def admin(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> dict[str, str]:
    await create_admin(sessionmaker, "admin@fsp.ru")
    return bearer(await login(client, "admin@fsp.ru"))


async def test_task_analytics_metrics_and_flags(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession], admin: dict[str, str]
) -> None:
    hot = (
        await client.post(f"{API}/admin/bank/tasks", headers=admin, json=quiz_task("Hot"))
    ).json()
    calm = (
        await client.post(f"{API}/admin/bank/tasks", headers=admin, json=quiz_task("Calm"))
    ).json()
    candidate = await _candidate(sessionmaker)
    now = datetime.now(UTC)

    # Week A, variant «a»: 3 full, 6 partial, 15 unsolved, 6 never answered, 1 expired.
    await _attempts(
        sessionmaker,
        candidate,
        hot["id"],
        started=now - timedelta(days=20),
        minutes=10,
        variant="a",
        grade=Grade.JUNIOR,
        points=[1.0] * 3 + [0.5] * 6 + [0.0] * 15 + [None] * 6,
        expired=1,
    )
    # Week B, variant «b»: 15 full, 15 unsolved — the share jumps by 40 points.
    await _attempts(
        sessionmaker,
        candidate,
        hot["id"],
        started=now - timedelta(days=10),
        minutes=25,
        variant="b",
        grade=Grade.MIDDLE,
        points=[1.0] * 15 + [0.0] * 15,
    )
    # Too few attempts for any flag.
    await _attempts(
        sessionmaker,
        candidate,
        calm["id"],
        started=now - timedelta(days=5),
        minutes=5,
        variant="a",
        grade=Grade.JUNIOR,
        points=[0.0] * 5,
    )

    empty = await client.get(f"{API}/admin/analytics/tasks", headers=admin)
    assert empty.json()["snapshot"] is None

    computed = await client.post(
        f"{API}/admin/analytics/tasks/recalculate", headers=admin, json={"period": "90d"}
    )
    assert computed.status_code == 200, computed.text
    rows = {row["taskId"]: row for row in computed.json()["result"]["tasks"]}

    row = rows[hot["id"]]
    assert row["attempts"] == 61
    assert row["fullShare"] == 29.5
    assert row["partialShare"] == 9.8
    assert row["abandonedShare"] == 11.5
    assert row["unsolvedShare"] == 49.2
    # Time counts for answered tasks only: 24 × 600 s and 30 × 1500 s.
    assert row["avgTimeSec"] == 1100
    assert row["medianTimeSec"] == 1500
    assert row["variantSpreadPp"] == 40.3
    assert row["maxWeeklyJumpPp"] == 40.3
    assert row["flags"] == ["out_of_target", "variant_spread", "possible_leak"]
    assert rows[calm["id"]]["attempts"] == 5
    assert rows[calm["id"]]["flags"] == []
    summary = computed.json()["result"]["summary"]
    assert summary["flags"] == {"out_of_target": 1, "variant_spread": 1, "possible_leak": 1}

    page = await client.get(f"{API}/admin/analytics/tasks?flag=possible_leak", headers=admin)
    assert [item["taskId"] for item in page.json()["items"]] == [hot["id"]]

    # The 7-day period sees only the calm task's attempts.
    week = await client.post(
        f"{API}/admin/analytics/tasks/recalculate", headers=admin, json={"period": "7d"}
    )
    week_rows = {row["taskId"]: row for row in week.json()["result"]["tasks"]}
    assert week_rows[hot["id"]]["attempts"] == 0
    assert week_rows[calm["id"]]["attempts"] == 5

    card = await client.post(
        f"{API}/admin/analytics/task_card/recalculate",
        headers=admin,
        json={"period": "90d", "taskId": hot["id"]},
    )
    assert card.status_code == 200, card.text
    result = card.json()["result"]
    assert {v["variant"]: v["fullShare"] for v in result["variants"]} == {"a": 9.7, "b": 50.0}
    assert {g["grade"]: g["attempts"] for g in result["grades"]} == {"junior": 31, "middle": 30}
    assert [w["fullShare"] for w in result["weekly"]] == [9.7, 50.0]
    assert sum(m["attempts"] for m in result["monthly"]) == 61
    assert {h["minute"]: h["count"] for h in result["histogram"]} == {10: 24, 25: 30}
    assert result["flags"] == ["out_of_target", "variant_spread", "possible_leak"]


async def test_recalculation_cooldown_and_csv(client: AsyncClient, admin: dict[str, str]) -> None:
    first = await client.post(
        f"{API}/admin/analytics/platform/recalculate", headers=admin, json={"period": "30d"}
    )
    again = await client.post(
        f"{API}/admin/analytics/platform/recalculate", headers=admin, json={"period": "30d"}
    )
    other = await client.post(
        f"{API}/admin/analytics/platform/recalculate", headers=admin, json={"period": "all"}
    )
    assert first.status_code == 200
    assert again.status_code == 429
    assert "nextAllowedAt" in again.json()["error"]["details"]
    # Other filters are another snapshot with its own cooldown.
    assert other.status_code == 200

    stored = await client.get(f"{API}/admin/analytics/snapshot/platform?period=30d", headers=admin)
    assert stored.json()["snapshot"]["id"] == first.json()["snapshot"]["id"]

    exported = await client.get(
        f"{API}/admin/analytics/platform/export.csv?period=30d&table=candidate_funnel",
        headers=admin,
    )
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("text/csv")
    body = exported.content.decode("utf-8")
    assert body.startswith("﻿Шаг;Количество;")
    assert "Регистрация;" in body

    missing = await client.get(
        f"{API}/admin/analytics/employers/export.csv?table=companies", headers=admin
    )
    assert missing.status_code == 404
