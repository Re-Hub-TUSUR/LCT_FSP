"""Analytics snapshots: computed only when an admin presses «Пересчитать», then stored.

- the same block with the same filters is recalculated at most once in `COOLDOWN`;
- while one calculation runs, a second one for the same key is refused, not queued:
  an in-process guard for one worker and a PostgreSQL advisory lock across workers.
"""

import hashlib
import json
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.analytics.employers import compute_employers
from app.admin.analytics.metrics import FlagRules
from app.admin.analytics.platform import compute_platform
from app.admin.analytics.sql import Dialect
from app.admin.analytics.tasks import compute_task_card, compute_task_table
from app.admin.enums import AnalyticsPeriod
from app.admin.models import AdminSnapshot
from app.admin.schemas import AnalyticsFilters, SnapshotMeta
from app.admin.services.parameters import ParameterService
from app.core.errors import AppError, ConflictError, NotFoundError, TooManyRequestsError
from app.models import AssessmentTask, User

COOLDOWN: Final = timedelta(minutes=5)
_RUNNING: set[str] = set()

type Compute = Callable[
    [AsyncSession, AnalyticsFilters, datetime | None, dict[str, int]],
    Awaitable[dict[str, Any]],
]


async def _tasks(
    session: AsyncSession, _: AnalyticsFilters, since: datetime | None, params: dict[str, int]
) -> dict[str, Any]:
    return await compute_task_table(session, since, FlagRules.from_parameters(params))


async def _task_card(
    session: AsyncSession, filters: AnalyticsFilters, since: datetime | None, params: dict[str, int]
) -> dict[str, Any]:
    if filters.task_id is None:
        raise AppError("Не указано задание")
    return await compute_task_card(
        session, filters.task_id, since, FlagRules.from_parameters(params)
    )


async def _platform(
    session: AsyncSession, _: AnalyticsFilters, since: datetime | None, __: dict[str, int]
) -> dict[str, Any]:
    return await compute_platform(session, since)


async def _employers(
    session: AsyncSession, _: AnalyticsFilters, since: datetime | None, params: dict[str, int]
) -> dict[str, Any]:
    return await compute_employers(session, since, params)


@dataclass(frozen=True, slots=True)
class BlockSpec:
    compute: Compute
    needs_task: bool = False


BLOCKS: Final[dict[str, BlockSpec]] = {
    "tasks": BlockSpec(_tasks),
    "task_card": BlockSpec(_task_card, needs_task=True),
    "platform": BlockSpec(_platform),
    "employers": BlockSpec(_employers),
}


def since_of(period: AnalyticsPeriod, now: datetime) -> datetime | None:
    days = period.days
    return now - timedelta(days=days) if days is not None else None


def _aware(value: datetime) -> datetime:
    # SQLite (tests) returns naive datetimes; they are stored in UTC.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def meta(snapshot: AdminSnapshot) -> SnapshotMeta:
    computed_at = _aware(snapshot.computed_at)
    return SnapshotMeta(
        id=snapshot.id,
        block=snapshot.block,
        filters=snapshot.filters,
        computed_at=computed_at,
        duration_ms=snapshot.duration_ms,
        next_allowed_at=computed_at + COOLDOWN,
    )


class SnapshotService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def normalize(self, block: str, filters: AnalyticsFilters) -> dict[str, Any]:
        """The filters that matter for the block, in a canonical form."""
        spec = BLOCKS.get(block)
        if spec is None:
            raise NotFoundError("Неизвестный блок аналитики")
        data: dict[str, Any] = {"period": filters.period.value}
        if spec.needs_task:
            if filters.task_id is None:
                raise AppError("Не указано задание")
            task = await self._session.get(AssessmentTask, filters.task_id)
            if task is None or task.owner_id is not None:
                raise NotFoundError("Задание не найдено")
            data["taskId"] = str(filters.task_id)
        return data

    async def latest(self, block: str, filters: AnalyticsFilters) -> AdminSnapshot | None:
        key = _key(await self.normalize(block, filters))
        return await self._latest(block, key)

    async def _latest(self, block: str, key: str) -> AdminSnapshot | None:
        return await self._session.scalar(
            select(AdminSnapshot)
            .where(AdminSnapshot.block == block, AdminSnapshot.filters_key == key)
            .order_by(AdminSnapshot.computed_at.desc())
            .limit(1)
        )

    async def recalculate(
        self, block: str, filters: AnalyticsFilters, actor: User
    ) -> AdminSnapshot:
        normalized = await self.normalize(block, filters)
        key = _key(normalized)
        guard = f"{block}|{key}"
        if guard in _RUNNING:
            raise ConflictError("Расчёт уже идёт")
        _RUNNING.add(guard)
        try:
            if Dialect.of(self._session).postgres:
                # Released with the transaction; `try` never waits for a concurrent calculation.
                locked = await self._session.scalar(
                    select(func.pg_try_advisory_xact_lock(_lock_id(guard)))
                )
                if not locked:
                    raise ConflictError("Расчёт уже идёт")
            # Checked under the lock: a calculation that has just finished elsewhere counts.
            previous = await self._latest(block, key)
            now = datetime.now(UTC)
            if previous is not None and now - _aware(previous.computed_at) < COOLDOWN:
                allowed_at = _aware(previous.computed_at) + COOLDOWN
                raise TooManyRequestsError(
                    "Эти данные пересчитывались меньше 5 минут назад",
                    details={"nextAllowedAt": allowed_at.isoformat()},
                )
            parameters = await ParameterService(self._session).values()
            started = time.perf_counter()
            result = await BLOCKS[block].compute(
                self._session,
                filters,
                since_of(AnalyticsPeriod(normalized["period"]), now),
                parameters,
            )
            snapshot = AdminSnapshot(
                id=uuid.uuid4(),
                block=block,
                filters_key=key,
                filters=normalized,
                result=result,
                computed_at=now,
                duration_ms=round((time.perf_counter() - started) * 1000),
                created_by=actor.id,
            )
            self._session.add(snapshot)
            # Committed here, before the guards are released: whoever comes next sees the
            # snapshot and its cooldown.
            await self._session.commit()
            return snapshot
        finally:
            _RUNNING.discard(guard)


def _key(filters: dict[str, Any]) -> str:
    return json.dumps(filters, sort_keys=True, separators=(",", ":"))


def _lock_id(guard: str) -> int:
    return int.from_bytes(hashlib.sha256(guard.encode()).digest()[:8], "big", signed=True)
