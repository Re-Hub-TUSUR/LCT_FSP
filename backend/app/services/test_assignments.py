"""Tests a company sends to a candidate after a match («тестовые»).

The company picks one of its own tests; the candidate takes it in the same runner as a grade
test; the company sees the answers, grades the open ones and gets the score. Such an attempt
never touches the candidate's categories or cooldowns.
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Final

from app.core.errors import AppError, ConflictError, NotFoundError
from app.models import (
    AssessmentAttempt,
    AssessmentTask,
    AssessmentTest,
    AssignmentStatus,
    AttemptStatus,
    CandidateProfile,
    Company,
    TestAssignment,
    User,
)
from app.repositories.assessment import AssessmentRepository
from app.repositories.candidate import CandidateRepository
from app.repositories.company import CompanyRepository
from app.repositories.reaction import ReactionRepository
from app.repositories.vacancy import VacancyRepository
from app.schemas.assessment import (
    AssignmentCreate,
    AssignmentDetail,
    AssignmentRead,
    AttemptDetail,
    FixedComposition,
    NamedRef,
    ReviewRequest,
    ReviewTask,
)
from app.services.assessment_bank import test_read
from app.services.assessments import AssessmentService, settle
from app.services.task_kinds import spec_of

DEFAULT_DUE: Final = timedelta(days=7)
# One live assignment of a test per candidate.
_LIVE: Final = (AssignmentStatus.SENT, AssignmentStatus.IN_PROGRESS, AssignmentStatus.REVIEW)
_GRADED: Final = (AttemptStatus.AWAITING_REVIEW, AttemptStatus.PASSED, AttemptStatus.FAILED)


def _aware(value: datetime) -> datetime:
    # SQLite returns naive datetimes; values are always stored in UTC.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


class TestAssignmentService:
    def __init__(
        self,
        repository: AssessmentRepository,
        companies: CompanyRepository,
        candidates: CandidateRepository,
        *,
        vacancies: VacancyRepository,
        reactions: ReactionRepository,
        assessments: AssessmentService,
    ) -> None:
        self._repository = repository
        self._companies = companies
        self._candidates = candidates
        self._vacancies = vacancies
        self._reactions = reactions
        self._assessments = assessments

    # ── Company ───────────────────────────────────────────────────────────────────────────

    async def send(self, user: User, data: AssignmentCreate) -> AssignmentRead:
        company = await self._companies.get_by_owner(user.id)
        if company is None:
            raise ConflictError("Сначала заполните профиль компании")
        test = await self._repository.get_test(data.test_id)
        if test is None or test.owner_id != user.id or not test.is_active:
            raise NotFoundError("Тест не найден")
        profile = await self._candidates.get(data.candidate_id)
        if profile is None or not profile.is_visible_to_employers:
            raise NotFoundError("Кандидат не найден")
        matched = await self._reactions.is_match(
            recruiter_id=user.id,
            company_id=company.id,
            candidate_id=profile.id,
            candidate_user_id=profile.user_id,
        )
        if not matched:
            raise ConflictError(
                "Тестовое можно отправить после взаимного интереса: вы добавили кандидата "
                "в избранное, а он отметил вакансию вашей компании"
            )
        if data.vacancy_id is not None:
            row = await self._vacancies.get(data.vacancy_id)
            if row is None or row[1].owner_id != user.id:
                raise NotFoundError("Вакансия не найдена")
        now = datetime.now(UTC)
        due_at = data.due_at.astimezone(UTC) if data.due_at else now + DEFAULT_DUE
        if due_at <= now:
            raise AppError("Срок тестового должен быть в будущем")
        tasks_count = await self._tasks_count(test)
        if tasks_count == 0:
            raise ConflictError("В тесте нет активных задач")
        sent = await self._settled(await self._repository.assignments(candidate_id=profile.id))
        if any(a.test_id == test.id and a.status in _LIVE for a in sent):
            raise ConflictError("Этот тест уже отправлен кандидату")

        assignment = await self._repository.add(
            TestAssignment(
                company_id=company.id,
                candidate_id=profile.id,
                test_id=test.id,
                vacancy_id=data.vacancy_id,
                title=test.title,
                duration_minutes=test.duration_minutes,
                tasks_count=tasks_count,
                message=(data.message or "").strip() or None,
                due_at=due_at,
                status=AssignmentStatus.SENT,
            )
        )
        return (await self._read([assignment]))[0]

    async def outgoing(self, user: User) -> list[AssignmentRead]:
        company = await self._companies.get_by_owner(user.id)
        if company is None:
            return []
        return await self._read(
            await self._settled(await self._repository.assignments(company_id=company.id))
        )

    async def detail(self, user: User, assignment_id: uuid.UUID) -> AssignmentDetail:
        assignment = await self._own(user, assignment_id)
        await self._settled([assignment])
        return await self._detail(assignment)

    async def review(
        self, user: User, assignment_id: uuid.UUID, data: ReviewRequest
    ) -> AssignmentDetail:
        """Grades hand-checked answers. Once none is left ungraded the attempt gets its score;
        a later review may change the grades and the score with them."""
        assignment = await self._own(user, assignment_id)
        await self._settled([assignment])
        attempt = await self._repository.attempt_of_assignment(assignment.id)
        if attempt is None or attempt.status not in _GRADED:
            raise ConflictError("Кандидат ещё не завершил этот тест")
        tasks = await self._tasks(attempt)
        by_id = {task.id: task for task in tasks}
        answers = await self._repository.answers_of(attempt.id)
        for grade in data.grades:
            task = by_id.get(grade.task_id)
            answer = answers.get(grade.task_id)
            if task is None or not spec_of(task).manual:
                raise AppError("Вручную оцениваются только открытые ответы этого теста")
            if answer is None:
                raise AppError("Кандидат не ответил на это задание: оно остаётся без баллов")
            answer.points = grade.points
            answer.comment = (grade.comment or "").strip() or None
            await self._repository.add(answer)

        if all(answer.points is not None for answer in answers.values()):
            points = {task.id: 0.0 for task in tasks}
            points.update({task_id: answer.points or 0.0 for task_id, answer in answers.items()})
            settle(attempt, tasks, points)
            await self._repository.add(attempt)
            await self._assessments.after_close(attempt)
        return await self._detail(assignment)

    async def revoke(self, user: User, assignment_id: uuid.UUID) -> None:
        assignment = await self._own(user, assignment_id)
        if assignment.status not in (
            AssignmentStatus.SENT,
            AssignmentStatus.DECLINED,
            AssignmentStatus.EXPIRED,
        ):
            raise ConflictError("Кандидат уже начал этот тест: отозвать его нельзя")
        await self._repository.delete(assignment)

    # ── Candidate ─────────────────────────────────────────────────────────────────────────

    async def incoming(self, user: User) -> list[AssignmentRead]:
        profile = await self._candidates.get_by_user(user.id)
        if profile is None:
            return []
        return await self._read(
            await self._settled(await self._repository.assignments(candidate_id=profile.id))
        )

    async def start(self, user: User, assignment_id: uuid.UUID) -> AttemptDetail:
        profile, assignment = await self._incoming(user, assignment_id)
        await self._settled([assignment])
        if assignment.status == AssignmentStatus.EXPIRED:
            raise ConflictError("Срок этого тестового истёк")
        if assignment.status != AssignmentStatus.SENT:
            raise ConflictError("Это тестовое уже начато или закрыто")
        test = await self._repository.get_test(assignment.test_id) if assignment.test_id else None
        if test is None or not test.is_active:
            raise ConflictError("Компания убрала этот тест")
        attempt = await self._assessments.start_assigned(profile, test, assignment)
        assignment.status = AssignmentStatus.IN_PROGRESS
        await self._repository.add(assignment)
        return attempt

    async def decline(self, user: User, assignment_id: uuid.UUID) -> AssignmentRead:
        _, assignment = await self._incoming(user, assignment_id)
        if assignment.status != AssignmentStatus.SENT:
            raise ConflictError("Отказаться можно только от тестового, которое ещё не начато")
        assignment.status = AssignmentStatus.DECLINED
        await self._repository.add(assignment)
        return (await self._read([assignment]))[0]

    # ── Helpers ───────────────────────────────────────────────────────────────────────────

    async def _own(self, user: User, assignment_id: uuid.UUID) -> TestAssignment:
        company = await self._companies.get_by_owner(user.id)
        assignment = await self._repository.get_assignment(assignment_id)
        if company is None or assignment is None or assignment.company_id != company.id:
            raise NotFoundError("Тестовое не найдено")
        return assignment

    async def _incoming(
        self, user: User, assignment_id: uuid.UUID
    ) -> tuple[CandidateProfile, TestAssignment]:
        profile = await self._candidates.get_by_user(user.id)
        assignment = await self._repository.get_assignment(assignment_id)
        if profile is None or assignment is None or assignment.candidate_id != profile.id:
            raise NotFoundError("Тестовое не найдено")
        return profile, assignment

    async def _settled(self, assignments: Sequence[TestAssignment]) -> Sequence[TestAssignment]:
        """Closes what time has decided: an unopened test past its due date, an attempt the
        candidate walked away from."""
        now = datetime.now(UTC)
        running = [a.id for a in assignments if a.status == AssignmentStatus.IN_PROGRESS]
        attempts = await self._repository.attempts_of_assignments(running)
        for assignment in assignments:
            if assignment.status == AssignmentStatus.SENT and now > _aware(assignment.due_at):
                assignment.status = AssignmentStatus.EXPIRED
                await self._repository.add(assignment)
            elif assignment.id in attempts:
                # Changes the assignment's status too when the attempt is closed.
                await self._assessments.close_abandoned(attempts[assignment.id])
        return assignments

    async def _tasks_count(self, test: AssessmentTest) -> int:
        composition = test_read(test).composition
        if not isinstance(composition, FixedComposition):
            return 0
        tasks = await self._repository.tasks_by_ids(composition.task_ids)
        return sum(task.is_active for task in tasks.values())

    async def _tasks(self, attempt: AssessmentAttempt) -> list[AssessmentTask]:
        ids = [uuid.UUID(task_id) for task_id in attempt.task_ids]
        tasks = await self._repository.tasks_by_ids(ids)
        return [tasks[task_id] for task_id in ids if task_id in tasks]

    async def _read(self, assignments: Sequence[TestAssignment]) -> list[AssignmentRead]:
        attempts = await self._repository.attempts_of_assignments([a.id for a in assignments])
        profiles = await self._candidates.by_ids({a.candidate_id for a in assignments})
        companies: dict[uuid.UUID, Company | None] = {}
        vacancies: dict[uuid.UUID, str | None] = {}
        result = []
        for assignment in assignments:
            if assignment.company_id not in companies:
                companies[assignment.company_id] = await self._companies.get(assignment.company_id)
            vacancy_id = assignment.vacancy_id
            if vacancy_id is not None and vacancy_id not in vacancies:
                row = await self._vacancies.get(vacancy_id)
                vacancies[vacancy_id] = row[0].title if row else None
            company = companies[assignment.company_id]
            profile = profiles.get(assignment.candidate_id)
            attempt = attempts.get(assignment.id)
            vacancy_title = vacancies.get(vacancy_id) if vacancy_id else None
            result.append(
                AssignmentRead(
                    id=assignment.id,
                    title=assignment.title,
                    status=assignment.status,
                    company=NamedRef(
                        id=assignment.company_id, name=company.name if company else ""
                    ),
                    candidate=NamedRef(
                        id=assignment.candidate_id, name=profile.display_name if profile else ""
                    ),
                    vacancy=NamedRef(id=vacancy_id, name=vacancy_title)
                    if vacancy_id and vacancy_title
                    else None,
                    message=assignment.message,
                    duration_minutes=assignment.duration_minutes,
                    tasks_count=assignment.tasks_count,
                    created_at=_aware(assignment.created_at),
                    due_at=_aware(assignment.due_at),
                    attempt_id=attempt.id if attempt else None,
                    finished_at=_aware(attempt.finished_at)
                    if attempt and attempt.finished_at
                    else None,
                    score=attempt.score if attempt else None,
                    pass_score=attempt.pass_score if attempt else None,
                )
            )
        return result

    async def _detail(self, assignment: TestAssignment) -> AssignmentDetail:
        base = (await self._read([assignment]))[0]
        attempt = await self._repository.attempt_of_assignment(assignment.id)
        review: list[ReviewTask] = []
        # Nothing of a running attempt is shown: the company sees the finished work only.
        if attempt is not None and attempt.status in _GRADED:
            answers = await self._repository.answers_of(attempt.id)
            for task in await self._tasks(attempt):
                spec = spec_of(task)
                answer = answers.get(task.id)
                review.append(
                    ReviewTask(
                        id=task.id,
                        kind=task.kind,
                        title=task.title,
                        statement=task.statement,
                        answered=answer is not None,
                        points=answer.points if answer else 0.0,
                        manual=spec.manual,
                        comment=answer.comment if answer else None,
                        review=spec.review(
                            spec.payload(task),
                            attempt.task_state.get(str(task.id)),
                            answer.answer if answer else None,
                        ),
                    )
                )
        return AssignmentDetail(
            **base.model_dump(),
            tasks=review,
            paste_count=attempt.paste_count if attempt else 0,
            blur_count=attempt.blur_count if attempt else 0,
        )
