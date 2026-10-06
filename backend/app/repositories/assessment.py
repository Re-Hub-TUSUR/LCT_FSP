import uuid
from collections.abc import Collection, Sequence

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentTask,
    AssessmentTest,
    CandidateCategory,
    CandidateProfile,
    Grade,
    TaskKind,
    TestAssignment,
)

type BankRow = AssessmentTask | AssessmentTest
type Row = (
    BankRow
    | AssessmentAttempt
    | AssessmentAnswer
    | CandidateProfile
    | CandidateCategory
    | TestAssignment
)


class AssessmentRepository:
    """Task bank, test templates and attempts. `owner_id=None` addresses the platform bank."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add[T: Row](self, row: T) -> T:
        self._session.add(row)
        await self._session.flush()
        return row

    async def delete(self, row: BankRow | TestAssignment) -> None:
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
        self,
        owner_id: uuid.UUID | None,
        *,
        kind: TaskKind | None = None,
        search: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[Sequence[AssessmentTask], int]:
        """Newest first. Without `limit` — the whole bank of the owner (export)."""
        conditions = [_owned(AssessmentTask, owner_id)]
        if kind is not None:
            conditions.append(AssessmentTask.kind == kind)
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(AssessmentTask.title.ilike(pattern), AssessmentTask.topic.ilike(pattern))
            )
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

    async def platform_test(self, grade: Grade, specialization: str) -> AssessmentTest | None:
        """The active platform template for a category.

        A template written for the specialization wins over the general one of the grade; among
        equals the newest one does.
        """
        result = await self._session.scalars(
            select(AssessmentTest)
            .where(
                AssessmentTest.owner_id.is_(None),
                AssessmentTest.grade == grade,
                AssessmentTest.is_active.is_(True),
                AssessmentTest.specialization.is_(None)
                | (AssessmentTest.specialization == specialization),
            )
            .order_by(
                AssessmentTest.specialization.is_(None),
                AssessmentTest.created_at.desc(),
                AssessmentTest.id,
            )
            .limit(1)
        )
        return result.first()

    async def platform_tests(self) -> Sequence[AssessmentTest]:
        """Every active grade template, newest first."""
        result = await self._session.scalars(
            select(AssessmentTest)
            .where(
                AssessmentTest.owner_id.is_(None),
                AssessmentTest.grade.is_not(None),
                AssessmentTest.is_active.is_(True),
            )
            .order_by(AssessmentTest.created_at.desc(), AssessmentTest.id)
        )
        return result.all()

    # ── Attempts ──────────────────────────────────────────────────────────────────────────

    async def get_attempt(
        self, attempt_id: uuid.UUID, *, lock: bool = False
    ) -> AssessmentAttempt | None:
        """`lock` holds the row until the transaction ends: two simultaneous "finish" requests
        grade the attempt once, the second one sees it already closed."""
        return await self._session.get(
            AssessmentAttempt, attempt_id, with_for_update=lock, populate_existing=lock
        )

    async def attempts_of(self, candidate_id: uuid.UUID) -> Sequence[AssessmentAttempt]:
        """Newest first."""
        result = await self._session.scalars(
            select(AssessmentAttempt)
            .where(AssessmentAttempt.candidate_id == candidate_id)
            .order_by(AssessmentAttempt.started_at.desc(), AssessmentAttempt.id)
        )
        return result.all()

    async def categories_of(self, candidate_id: uuid.UUID) -> dict[str, CandidateCategory]:
        """Confirmed categories by specialization."""
        result = await self._session.scalars(
            select(CandidateCategory).where(CandidateCategory.candidate_id == candidate_id)
        )
        return {category.specialization: category for category in result}

    async def attempt_of_assignment(self, assignment_id: uuid.UUID) -> AssessmentAttempt | None:
        result = await self._session.scalars(
            select(AssessmentAttempt)
            .where(AssessmentAttempt.assignment_id == assignment_id)
            .order_by(AssessmentAttempt.started_at.desc())
            .limit(1)
        )
        return result.first()

    async def answers_of(self, attempt_id: uuid.UUID) -> dict[uuid.UUID, AssessmentAnswer]:
        result = await self._session.scalars(
            select(AssessmentAnswer).where(AssessmentAnswer.attempt_id == attempt_id)
        )
        return {answer.task_id: answer for answer in result}

    # ── Assignments ───────────────────────────────────────────────────────────────────────

    async def get_assignment(self, assignment_id: uuid.UUID) -> TestAssignment | None:
        return await self._session.get(TestAssignment, assignment_id)

    async def assignments(
        self,
        *,
        company_id: uuid.UUID | None = None,
        candidate_id: uuid.UUID | None = None,
    ) -> Sequence[TestAssignment]:
        """Assignments of one side, newest first."""
        statement = select(TestAssignment).order_by(
            TestAssignment.created_at.desc(), TestAssignment.id
        )
        if company_id is not None:
            statement = statement.where(TestAssignment.company_id == company_id)
        if candidate_id is not None:
            statement = statement.where(TestAssignment.candidate_id == candidate_id)
        result = await self._session.scalars(statement)
        return result.all()

    async def attempts_of_assignments(
        self, assignment_ids: Collection[uuid.UUID]
    ) -> dict[uuid.UUID, AssessmentAttempt]:
        if not assignment_ids:
            return {}
        result = await self._session.scalars(
            select(AssessmentAttempt).where(AssessmentAttempt.assignment_id.in_(assignment_ids))
        )
        return {a.assignment_id: a for a in result if a.assignment_id is not None}


def _owned(
    model: type[AssessmentTask] | type[AssessmentTest], owner_id: uuid.UUID | None
) -> ColumnElement[bool]:
    return model.owner_id.is_(None) if owner_id is None else model.owner_id == owner_id
