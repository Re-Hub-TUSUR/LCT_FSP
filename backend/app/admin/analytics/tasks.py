"""Task analytics: how candidates do on every task of the platform bank.

A "fact" is one task inside one settled attempt. Its outcome:
- abandoned: the attempt ran out of time, or the candidate never sent an answer to the task;
- full / partial: the answer earned the whole task / a part of it;
- unsolved: answered and earned nothing.

Time is how long the task was on the candidate's screen (ssessment_task_times), counted for
answered tasks only; attempts recorded before the runner reported it have no time.
A variant is `task_state[task]["variant"]` of the attempt; attempts without it count as the
base variant.
"""

import uuid
from collections.abc import Sequence
from datetime import date, datetime
from enum import Enum
from typing import Any, Final

from sqlalchemy import Subquery, and_, case, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.admin.analytics.metrics import FlagRules, TaskFlag, outcome_shares, task_flags
from app.admin.analytics.sql import Dialect, Expr, medians
from app.admin.models import AdminTaskMeta
from app.admin.tasks_status import status_of
from app.models import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentTask,
    AssessmentTaskTime,
    AttemptStatus,
)

SETTLED: Final = (AttemptStatus.PASSED, AttemptStatus.FAILED, AttemptStatus.EXPIRED)
# Points are a float share: anything this close to 1 is the whole task.
FULL: Final = 0.999
# Time histogram: one-minute buckets, the last one holds everything longer.
HISTOGRAM_MINUTES: Final = 60
# A spread needs at least two variants to compare.
MIN_VARIANTS: Final = 2

_KEY_NAMES: Final = {
    "task_key": "taskId",
    "grade": "grade",
    "variant": "variant",
    "week": "week",
    "month": "month",
    "bucket": "minute",
}


def task_facts(dialect: Dialect, since: datetime | None, task_id: uuid.UUID | None) -> Subquery:
    attempt = AssessmentAttempt
    answer = aliased(AssessmentAnswer)
    spent = aliased(AssessmentTaskTime)
    elements = dialect.json_elements(attempt.task_ids)
    key: Expr = elements.c.value
    task_uuid = dialect.uuid_of_text(key)
    expired = attempt.status == AttemptStatus.EXPIRED
    abandoned = or_(expired, answer.id.is_(None))
    # Time to an answer: a task left without one has no solving time to compare.
    duration = case((abandoned, None), else_=spent.seconds)

    statement = (
        select(
            key.label("task_key"),
            attempt.id.label("attempt_id"),
            attempt.grade.label("grade"),
            dialect.json_member_text(attempt.task_state, key, "variant").label("variant"),
            dialect.week(attempt.started_at).label("week"),
            dialect.month(attempt.started_at).label("month"),
            duration.label("duration"),
            case(
                (duration.is_(None), None),
                (duration >= HISTOGRAM_MINUTES * 60, HISTOGRAM_MINUTES),
                else_=dialect.whole_minutes(duration),
            ).label("bucket"),
            case((abandoned, 1), else_=0).label("abandoned"),
            case((and_(~abandoned, answer.points >= FULL), 1), else_=0).label("full"),
            case((and_(~abandoned, answer.points > 0, answer.points < FULL), 1), else_=0).label(
                "partial"
            ),
        )
        .select_from(attempt)
        .join(elements, true())
        .join(
            AssessmentTask,
            and_(AssessmentTask.id == task_uuid, AssessmentTask.owner_id.is_(None)),
        )
        .outerjoin(answer, and_(answer.attempt_id == attempt.id, answer.task_id == task_uuid))
        .outerjoin(spent, and_(spent.attempt_id == attempt.id, spent.task_id == task_uuid))
        .where(attempt.status.in_(SETTLED), attempt.finished_at.is_not(None))
    )
    if since is not None:
        statement = statement.where(attempt.started_at >= since)
    if task_id is not None:
        statement = statement.where(AssessmentTask.id == task_id)
    return statement.subquery("facts")


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime | date):
        return value.isoformat()[:10]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


async def aggregate(
    session: AsyncSession, dialect: Dialect, facts: Subquery, keys: Sequence[str]
) -> list[dict[str, Any]]:
    """Outcome shares, mean and median time per group of `keys`, ordered by the keys."""
    group = [facts.c[key] for key in keys]
    statement = (
        select(
            *group,
            func.count().label("attempts"),
            func.sum(facts.c.full).label("full"),
            func.sum(facts.c.partial).label("partial"),
            func.sum(facts.c.abandoned).label("abandoned"),
            func.avg(facts.c.duration).label("avg_time"),
        )
        .group_by(*group)
        .order_by(*group)
    )
    rows = (await session.execute(statement)).all()
    middle = await medians(session, dialect, facts, "duration", keys)
    result = []
    for row in rows:
        values = tuple(row[: len(keys)])
        attempts, full, partial, abandoned, avg_time = row[len(keys) :]
        median = middle.get(values)
        item = {_KEY_NAMES[key]: _plain(value) for key, value in zip(keys, values, strict=True)}
        item.update(
            outcome_shares(int(attempts), int(full or 0), int(partial or 0), int(abandoned or 0))
        )
        item["avgTimeSec"] = round(float(avg_time)) if avg_time is not None else None
        item["medianTimeSec"] = round(median) if median is not None else None
        result.append(item)
    return result


def _shares(facts: Subquery, keys: Sequence[str]) -> Subquery:
    group = [facts.c[key] for key in keys]
    return (
        select(
            *group,
            func.count().label("attempts"),
            (100.0 * func.sum(facts.c.full) / func.count()).label("share"),
        )
        .group_by(*group)
        .subquery()
    )


async def variant_spread(
    session: AsyncSession, facts: Subquery, min_attempts: int
) -> dict[str, float]:
    """Max − min full-solve share between the variants of a task, in percentage points.
    Only variants with enough attempts are compared; a task needs two of them."""
    per_variant = _shares(facts, ["task_key", "variant"])
    statement = (
        select(
            per_variant.c.task_key,
            (func.max(per_variant.c.share) - func.min(per_variant.c.share)).label("spread"),
        )
        .where(per_variant.c.attempts >= min_attempts)
        .group_by(per_variant.c.task_key)
        .having(func.count() >= MIN_VARIANTS)
    )
    rows = (await session.execute(statement)).all()
    return {str(row.task_key): round(float(row.spread), 1) for row in rows}


async def weekly_jump(
    session: AsyncSession, facts: Subquery, min_attempts: int
) -> dict[str, float]:
    """The biggest rise of the full-solve share from one week to the next one with attempts,
    in percentage points. Both weeks need enough attempts."""
    weekly = _shares(facts, ["task_key", "week"])
    lagged = select(
        weekly.c.task_key,
        weekly.c.share,
        weekly.c.attempts,
        func.lag(weekly.c.share)
        .over(partition_by=weekly.c.task_key, order_by=weekly.c.week)
        .label("previous_share"),
        func.lag(weekly.c.attempts)
        .over(partition_by=weekly.c.task_key, order_by=weekly.c.week)
        .label("previous_attempts"),
    ).subquery()
    statement = (
        select(
            lagged.c.task_key,
            func.max(lagged.c.share - lagged.c.previous_share).label("jump"),
        )
        .where(
            lagged.c.attempts >= min_attempts,
            lagged.c.previous_attempts >= min_attempts,
        )
        .group_by(lagged.c.task_key)
    )
    rows = (await session.execute(statement)).all()
    return {str(row.task_key): round(float(row.jump), 1) for row in rows if row.jump is not None}


async def compute_task_table(
    session: AsyncSession, since: datetime | None, rules: FlagRules
) -> dict[str, Any]:
    """Every platform task with its metrics and flags for the period."""
    dialect = Dialect.of(session)
    facts = task_facts(dialect, since, None)
    stats = {
        item["taskId"]: item for item in await aggregate(session, dialect, facts, ["task_key"])
    }
    spreads = await variant_spread(session, facts, rules.min_attempts)
    jumps = await weekly_jump(session, facts, rules.min_attempts)

    tasks = (
        await session.execute(
            select(AssessmentTask, AdminTaskMeta)
            .outerjoin(AdminTaskMeta, AdminTaskMeta.task_id == AssessmentTask.id)
            .where(AssessmentTask.owner_id.is_(None))
            .order_by(AssessmentTask.created_at.desc(), AssessmentTask.id)
        )
    ).all()
    rows = []
    flag_counts = dict.fromkeys((flag.value for flag in TaskFlag), 0)
    for task, meta in tasks:
        key = str(task.id)
        stat = stats.get(key) or outcome_shares(0, 0, 0, 0) | {
            "avgTimeSec": None,
            "medianTimeSec": None,
        }
        flags = task_flags(
            rules,
            attempts=stat["attempts"],
            full_share=stat["fullShare"],
            variant_spread_pp=spreads.get(key),
            max_weekly_jump_pp=jumps.get(key),
        )
        for flag in flags:
            flag_counts[flag.value] += 1
        rows.append(
            {
                **stat,
                "taskId": key,
                "title": task.title,
                "kind": task.kind.value,
                "specializations": list(task.specializations),
                "skill": task.topic,
                "grade": meta.grade if meta else None,
                "status": status_of(task, meta).value,
                "variantSpreadPp": spreads.get(key),
                "maxWeeklyJumpPp": jumps.get(key),
                "flags": [flag.value for flag in flags],
            }
        )
    return {
        "tasks": rows,
        "summary": {
            "tasks": len(rows),
            "withAttempts": sum(1 for row in rows if row["attempts"]),
            "flags": flag_counts,
        },
        "rules": {
            "minAttempts": rules.min_attempts,
            "targetMin": rules.target_min,
            "targetMax": rules.target_max,
            "spreadPp": rules.spread_pp,
            "leakPp": rules.leak_pp,
        },
    }


async def compute_task_card(
    session: AsyncSession, task_id: uuid.UUID, since: datetime | None, rules: FlagRules
) -> dict[str, Any]:
    """One task in detail: per variant, per declared grade, by week, by month, time histogram."""
    dialect = Dialect.of(session)
    facts = task_facts(dialect, since, task_id)
    all_time = task_facts(dialect, None, task_id)
    total = await aggregate(session, dialect, facts, [])
    overall = total[0] if total and total[0]["attempts"] else None
    spreads = await variant_spread(session, facts, rules.min_attempts)
    jumps = await weekly_jump(session, facts, rules.min_attempts)
    key = str(task_id)
    flags = (
        task_flags(
            rules,
            attempts=overall["attempts"],
            full_share=overall["fullShare"],
            variant_spread_pp=spreads.get(key),
            max_weekly_jump_pp=jumps.get(key),
        )
        if overall
        else []
    )
    histogram_rows = (
        await session.execute(
            select(facts.c.bucket, func.count().label("hits"))
            .where(facts.c.bucket.is_not(None))
            .group_by(facts.c.bucket)
            .order_by(facts.c.bucket)
        )
    ).all()
    return {
        "taskId": key,
        "overall": overall,
        "flags": [flag.value for flag in flags],
        "variantSpreadPp": spreads.get(key),
        "maxWeeklyJumpPp": jumps.get(key),
        "variants": [
            {**row, "variant": row["variant"] or "base"}
            for row in await aggregate(session, dialect, facts, ["variant"])
        ],
        "grades": await aggregate(session, dialect, facts, ["grade"]),
        "weekly": await aggregate(session, dialect, facts, ["week"]),
        "monthly": await aggregate(session, dialect, all_time, ["month"]),
        "histogram": [
            {"minute": int(row.bucket), "count": int(row.hits)} for row in histogram_rows
        ],
    }
