import uuid
from collections.abc import Collection, Sequence

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentTask,
    AssessmentTest,
    CandidateProfile,
    Grade,
    TaskKind,
)

type BankRow = AssessmentTask | AssessmentTest
type Row = BankRow | AssessmentAttempt | AssessmentAnswer | CandidateProfile


class AssessmentRepository:
    """Task bank, test templates and attempts. `owner_id=None` addresses the platform bank."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add[T: Row](self, row: T) -> T:
        self._session.add(row)
        await self._session.flush()
        return row

    async def delete(self, row: BankRow) -> None:
        await self._session.delete(row)
        await self._session.flush()

    # ── Bank ──────────────────────────────────────────────────────────────────────────────

    async def get_task(self, task_id: uuid.UUID) -> AssessmentTask | None:
        return await self._session.get(AssessmentTask, task_id)

    async def tasks_by_ids(self, ids: Collection[uuid.UUID]) -> dict[uuid.UUID, AssessmentTask]:
        if not ids:
            return {}
        result = await self._session.scalars(
            select(AssessmentTask).where(AssessmentTask.id.in_(ids))
        )
        return {task.id: task for task in result}

    async def list_tasks(
        self, owner_id: uuid.UUID | None, *, kind: TaskKind | None, limit: int, offset: int
    ) -> tuple[Sequence[AssessmentTask], int]:
        conditions = [_owned(AssessmentTask, owner_id)]
        if kind is not None:
            conditions.append(AssessmentTask.kind == kind)
        total = await self._session.scalar(
            select(func.count()).select_from(AssessmentTask).where(*conditions)
        )
        result = await self._session.scalars(
            select(AssessmentTask)
            .where(*conditions)
            .order_by(AssessmentTask.created_at.desc(), AssessmentTask.id)
            .limit(limit)
            .offset(offset)
        )
        return result.all(), total or 0

    async def platform_pool(self) -> Sequence[AssessmentTask]:
        """Every active platform task: variants are drawn from it in memory."""
        result = await self._session.scalars(
            select(AssessmentTask).where(
                AssessmentTask.owner_id.is_(None), AssessmentTask.is_active.is_(True)
            )
        )
        return result.all()

    async def get_test(self, test_id: uuid.UUID) -> AssessmentTest | None:
        return await self._session.get(AssessmentTest, test_id)

    async def list_tests(self, owner_id: uuid.UUID | None) -> Sequence[AssessmentTest]:
        result = await self._session.scalars(
            select(AssessmentTest)
            .where(_owned(AssessmentTest, owner_id))
            .order_by(AssessmentTest.created_at.desc(), AssessmentTest.id)
        )
        return result.all()

    async def platform_test(self, grade: Grade) -> AssessmentTest | None:
        """The active platform template for a grade; the newest one wins."""
        result = await self._session.scalars(
            select(AssessmentTest)
            .where(
                AssessmentTest.owner_id.is_(None),
                AssessmentTest.grade == grade,
                AssessmentTest.is_active.is_(True),
            )
            .order_by(AssessmentTest.created_at.desc(), AssessmentTest.id)
            .limit(1)
        )
        return result.first()

    # ── Attempts ──────────────────────────────────────────────────────────────────────────

    async def get_attempt(self, attempt_id: uuid.UUID) -> AssessmentAttempt | None:
        return await self._session.get(AssessmentAttempt, attempt_id)

    async def attempts_of(self, candidate_id: uuid.UUID) -> Sequence[AssessmentAttempt]:
        """Newest first."""
        result = await self._session.scalars(
            select(AssessmentAttempt)
            .where(AssessmentAttempt.candidate_id == candidate_id)
            .order_by(AssessmentAttempt.started_at.desc(), AssessmentAttempt.id)
        )
        return result.all()

    async def answers_of(self, attempt_id: uuid.UUID) -> dict[uuid.UUID, AssessmentAnswer]:
        result = await self._session.scalars(
            select(AssessmentAnswer).where(AssessmentAnswer.attempt_id == attempt_id)
        )
        return {answer.task_id: answer for answer in result}


def _owned(
    model: type[AssessmentTask] | type[AssessmentTest], owner_id: uuid.UUID | None
) -> ColumnElement[bool]:
    return model.owner_id.is_(None) if owner_id is None else model.owner_id == owner_id
