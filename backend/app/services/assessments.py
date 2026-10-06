"""Candidate side of testing: draw a variant, collect answers, run code, score, set the category.

What a task shows, accepts and earns is decided by its kind (`app.services.task_kinds`); this
module only drives the attempt. An attempt belongs either to a platform grade test (it confirms
a category and starts a cooldown) or to a test a company assigned (it does neither).
"""

import asyncio
import secrets
import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Final

from app.core.config import Settings
from app.core.errors import AppError, ConflictError, NotFoundError, TooManyRequestsError
from app.models import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentStatus,
    AssessmentTask,
    AssessmentTest,
    AssignmentStatus,
    AttemptStatus,
    CandidateCategory,
    CandidateProfile,
    Grade,
    TaskKind,
    TestAssignment,
    User,
)
from app.repositories.assessment import AssessmentRepository
from app.repositories.candidate import CandidateRepository
from app.schemas.assessment import (
    AssessmentStatusRead,
    AttemptAnswer,
    AttemptDetail,
    AttemptRead,
    AttemptSignal,
    AttemptStart,
    AttemptTask,
    FixedComposition,
    RulesComposition,
    RunRequest,
    RunResponse,
    RunResult,
    TemplateRead,
    TopicResult,
    TrackRead,
)
from app.services.assessment_bank import test_read
from app.services.categories import SPECIALIZATIONS, category_for
from app.services.code_runner import CodeRunner, CodeRunnerUnavailableError
from app.services.task_kinds import REGISTRY, spec_of
from app.services.task_kinds.code import CodeKind, judge

MAX_RUNS: Final = 20
RUN_INTERVAL: Final = timedelta(seconds=5)
# A finished-late attempt is still scored; an untouched one is closed after this slack.
ABANDON_AFTER: Final = timedelta(minutes=5)

_random = secrets.SystemRandom()


class AttemptExpiredError(ConflictError):
    code = "attempt_expired"
    default_message = "Время теста вышло"


def _aware(value: datetime) -> datetime:
    # SQLite returns naive datetimes; values are always stored in UTC.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


class AssessmentService:
    def __init__(
        self,
        repository: AssessmentRepository,
        candidates: CandidateRepository,
        runner: CodeRunner,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._candidates = candidates
        self._runner = runner
        self._settings = settings

    # ── Status and start ──────────────────────────────────────────────────────────────────

    async def status(self, user: User) -> AssessmentStatusRead:
        profile = await self._candidates.get_by_user(user.id)
        if profile is None:
            return AssessmentStatusRead(
                status=AssessmentStatus.NOT_TAKEN,
                specialization=None,
                grade=None,
                score=None,
                next_attempt_at=None,
                tracks=[],
                active_attempt_id=None,
                code_runner_available=self._runner.available,
                history=[],
            )
        attempts = await self._settled_attempts(profile)
        categories = await self._repository.categories_of(profile.id)
        active = next((a for a in attempts if a.status == AttemptStatus.IN_PROGRESS), None)
        # Confirmed specializations first, then the ones tried without success.
        tried = [a.specialization for a in attempts if a.specialization and a.finished_at]
        tracks = [
            _track(profile, specialization, categories.get(specialization), attempts)
            for specialization in dict.fromkeys([*categories, *tried])
        ]
        primary = next((track for track in tracks if track.is_primary), None)
        return AssessmentStatusRead(
            status=profile.assessment_status,
            specialization=primary.specialization if primary else None,
            grade=primary.grade if primary else None,
            score=primary.score if primary else None,
            next_attempt_at=primary.next_attempt_at if primary else None,
            tracks=tracks,
            active_attempt_id=active.id if active else None,
            code_runner_available=self._runner.available,
            history=[_attempt_read(attempt) for attempt in attempts],
        )

    async def templates(self) -> list[TemplateRead]:
        """What every grade test consists of. A fixed list is counted by its tasks."""
        result: list[TemplateRead] = []
        seen: set[tuple[Grade, str | None]] = set()
        for test in await self._repository.platform_tests():
            # Newest first: older templates of the same category are shadowed.
            if test.grade is None or (test.grade, test.specialization) in seen:
                continue
            seen.add((test.grade, test.specialization))
            composition = test_read(test).composition
            counts: dict[TaskKind, int] = defaultdict(int)
            if isinstance(composition, FixedComposition):
                tasks = await self._repository.tasks_by_ids(composition.task_ids)
                for task in tasks.values():
                    counts[task.kind] += task.is_active
            else:
                for rule in composition.rules:
                    counts[rule.kind] += rule.count
            result.append(
                TemplateRead(
                    grade=test.grade,
                    specialization=test.specialization,
                    duration_minutes=test.duration_minutes,
                    pass_score=test.pass_score,
                    tasks={kind: count for kind, count in counts.items() if count},
                    retry_days=self._retry_days(test),
                    grade_change_days=self._grade_change_days(test),
                )
            )
        return result

    async def set_primary(self, user: User, specialization: str) -> AssessmentStatusRead:
        """Makes a confirmed category the one employers see in search and feeds."""
        profile = await self._candidates.get_by_user(user.id)
        category = (
            (await self._repository.categories_of(profile.id)).get(specialization)
            if profile
            else None
        )
        if profile is None or category is None:
            raise NotFoundError("Эта специализация ещё не подтверждена тестом")
        _mirror(profile, category)
        await self._repository.add(profile)
        return await self.status(user)

    async def start(self, user: User, data: AttemptStart) -> AttemptDetail:
        if data.specialization not in SPECIALIZATIONS:
            raise AppError("Неизвестная специализация")
        profile = await self._profile(user)
        attempts = await self._settled_attempts(profile)
        if any(attempt.status == AttemptStatus.IN_PROGRESS for attempt in attempts):
            raise ConflictError("У вас уже есть незавершённый тест")
        categories = await self._repository.categories_of(profile.id)
        allowed_at = _next_attempt_at(
            data.specialization, categories.get(data.specialization), attempts
        )
        if allowed_at is not None:
            raise ConflictError(
                "Повторная попытка по этой специализации пока недоступна",
                details={"nextAttemptAt": allowed_at},
            )
        test = await self._repository.platform_test(data.grade, data.specialization)
        if test is None:
            raise ConflictError("Тест для этого грейда ещё не подготовлен")

        seen = {task_id for attempt in attempts for task_id in attempt.task_ids}
        tasks = await self._compose(test, data.specialization, seen)
        if not tasks:
            raise ConflictError("Банк задач для этой специализации пока пуст")
        if not self._runner.available and any(spec_of(task).code_group for task in tasks):
            # Most of the score would be out of reach: better not to burn the attempt.
            raise CodeRunnerUnavailableError(
                "Проверка кода сейчас недоступна, тест с задачей на код начать нельзя"
            )

        category = category_for(data.specialization, data.grade)
        return await self._open(
            profile,
            test,
            tasks,
            title=category.label if category else test.title,
            specialization=data.specialization,
            grade=data.grade,
        )

    async def start_assigned(
        self, profile: CandidateProfile, test: AssessmentTest, assignment: TestAssignment
    ) -> AttemptDetail:
        """Starts a test a company sent. No category, no cooldown: only the «one test at a
        time» rule is shared with grade tests."""
        attempts = await self._settled_attempts(profile)
        if any(attempt.status == AttemptStatus.IN_PROGRESS for attempt in attempts):
            raise ConflictError("У вас уже есть незавершённый тест")
        tasks = await self._compose(test, "", set())
        if not tasks:
            raise ConflictError("В этом тесте не осталось доступных задач")
        if not self._runner.available and any(spec_of(task).code_group for task in tasks):
            raise CodeRunnerUnavailableError(
                "Проверка кода сейчас недоступна, тест с задачей на код начать нельзя"
            )
        return await self._open(
            profile,
            test,
            tasks,
            title=assignment.title,
            specialization=None,
            grade=None,
            assignment_id=assignment.id,
        )

    async def _open(
        self,
        profile: CandidateProfile,
        test: AssessmentTest,
        tasks: Sequence[AssessmentTask],
        *,
        title: str,
        specialization: str | None,
        grade: Grade | None,
        assignment_id: uuid.UUID | None = None,
    ) -> AttemptDetail:
        now = datetime.now(UTC)
        states = {
            str(task.id): spec_of(task).new_state(spec_of(task).payload(task)) for task in tasks
        }
        attempt = await self._repository.add(
            AssessmentAttempt(
                candidate_id=profile.id,
                test_id=test.id,
                assignment_id=assignment_id,
                title=title,
                specialization=specialization,
                grade=grade,
                status=AttemptStatus.IN_PROGRESS,
                pass_score=test.pass_score,
                quiz_weight=test.quiz_weight,
                retry_days=self._retry_days(test),
                grade_change_days=self._grade_change_days(test),
                started_at=now,
                expires_at=now + timedelta(minutes=test.duration_minutes),
                task_ids=[str(task.id) for task in tasks],
                task_state={key: state for key, state in states.items() if state is not None},
            )
        )
        return self._detail(attempt, tasks, {})

    # ── Working on an attempt ─────────────────────────────────────────────────────────────

    async def read(self, user: User, attempt_id: uuid.UUID) -> AttemptDetail:
        attempt = await self._attempt(user, attempt_id)
        tasks = await self._tasks(attempt)
        return self._detail(attempt, tasks, await self._repository.answers_of(attempt.id))

    async def answer(self, user: User, attempt_id: uuid.UUID, data: AttemptAnswer) -> None:
        attempt = await self._running_attempt(user, attempt_id)
        task = await self._task(attempt, data.task_id)
        spec = spec_of(task)
        value = spec.store_answer(
            spec.payload(task), attempt.task_state.get(str(task.id)), data.answer
        )

        saved = (await self._repository.answers_of(attempt.id)).get(task.id)
        if saved is None:
            saved = AssessmentAnswer(attempt_id=attempt.id, task_id=task.id)
        saved.answer = value
        await self._repository.add(saved)

    async def run(self, user: User, attempt_id: uuid.UUID, data: RunRequest) -> RunResponse:
        attempt = await self._running_attempt(user, attempt_id)
        task = await self._task(attempt, data.task_id)
        spec = spec_of(task)
        if not isinstance(spec, CodeKind):
            raise AppError("Запуск доступен только для задач на код")
        payload = spec.payload(task)
        spec.check_language(payload, data.language)

        now = datetime.now(UTC)
        if attempt.runs_count >= MAX_RUNS:
            raise TooManyRequestsError("Лимит запусков в этом тесте исчерпан")
        if attempt.last_run_at and now - _aware(attempt.last_run_at) < RUN_INTERVAL:
            raise TooManyRequestsError("Запускать код можно раз в несколько секунд")
        attempt.runs_count += 1
        attempt.last_run_at = now
        await self._repository.add(attempt)

        if data.input is not None:
            execution = await self._runner.run(
                compiler=data.language, code=data.code, stdin=data.input
            )
            results = [
                RunResult(
                    verdict=None,
                    input=data.input,
                    expected=None,
                    output=execution.output,
                    error=execution.error,
                    time=execution.time,
                )
            ]
        else:
            # Only the open groups: hidden ones are kept for the final check.
            groups = [group for group in payload.groups if not group.hidden]
            executions = await asyncio.gather(
                *(
                    self._runner.run(compiler=data.language, code=data.code, stdin=group.input)
                    for group in groups
                )
            )
            results = [
                RunResult(
                    verdict=judge(execution, group.expected, payload.time_limit),
                    input=group.input,
                    expected=group.expected,
                    output=execution.output,
                    error=execution.error,
                    time=execution.time,
                )
                for group, execution in zip(groups, executions, strict=True)
            ]
        return RunResponse(results=results, runs_left=MAX_RUNS - attempt.runs_count)

    async def signal(self, user: User, attempt_id: uuid.UUID, data: AttemptSignal) -> None:
        attempt = await self._attempt(user, attempt_id)
        if attempt.status != AttemptStatus.IN_PROGRESS:
            return
        if data.kind == "paste":
            attempt.paste_count += 1
        else:
            attempt.blur_count += 1
        await self._repository.add(attempt)

    # ── Finish ────────────────────────────────────────────────────────────────────────────

    async def finish(self, user: User, attempt_id: uuid.UUID) -> AttemptRead:
        """Scores the saved answers. Allowed after the deadline too: nothing new can be saved
        once the time is out, so finishing late gives no advantage."""
        attempt = await self._attempt(user, attempt_id)
        if attempt.status != AttemptStatus.IN_PROGRESS:
            return _attempt_read(attempt)
        await self._close(attempt, finished_at=datetime.now(UTC))
        return _attempt_read(attempt)

    async def _close(self, attempt: AssessmentAttempt, *, finished_at: datetime) -> None:
        """Grades what is saved. Answers only a person can grade leave the attempt
        `awaiting_review`: its score appears once they are all graded."""
        tasks = await self._tasks(attempt)
        answers = await self._repository.answers_of(attempt.id)
        earned = await asyncio.gather(*(self._points(task, answers.get(task.id)) for task in tasks))
        points = dict(zip((task.id for task in tasks), earned, strict=True))
        for task_id, answer in answers.items():
            answer.points = points.get(task_id, 0.0)
            await self._repository.add(answer)

        attempt.finished_at = finished_at
        if any(value is None for value in points.values()):
            attempt.status = AttemptStatus.AWAITING_REVIEW
        else:
            settle(attempt, tasks, {task_id: value or 0.0 for task_id, value in points.items()})
        await self._repository.add(attempt)
        await self.after_close(attempt)

    async def close_abandoned(self, attempt: AssessmentAttempt) -> None:
        """Closes an assigned attempt the candidate left past its deadline, grading what was
        saved: the company still wants to see it."""
        if (
            attempt.assignment_id is not None
            and attempt.status == AttemptStatus.IN_PROGRESS
            and datetime.now(UTC) > _aware(attempt.expires_at) + ABANDON_AFTER
        ):
            await self._close(attempt, finished_at=attempt.expires_at)

    async def after_close(self, attempt: AssessmentAttempt) -> None:
        """What a closed (or just reviewed) attempt changes outside itself."""
        if attempt.assignment_id is not None:
            assignment = await self._repository.get_assignment(attempt.assignment_id)
            if assignment is not None:
                assignment.status = (
                    AssignmentStatus.REVIEW
                    if attempt.status == AttemptStatus.AWAITING_REVIEW
                    else AssignmentStatus.DONE
                )
                await self._repository.add(assignment)
            return
        profile = await self._candidates.get(attempt.candidate_id)
        if profile is not None and attempt.grade is not None and attempt.specialization:
            if attempt.status == AttemptStatus.PASSED:
                await self._confirm(profile, attempt)
            elif profile.assessment_status != AssessmentStatus.PASSED:
                # A failed test assigns nothing; confirmed categories stay as they were.
                profile.assessment_status = AssessmentStatus.FAILED

    async def _confirm(self, profile: CandidateProfile, attempt: AssessmentAttempt) -> None:
        """Records the confirmed grade of the attempt's specialization."""
        if attempt.grade is None or not attempt.specialization or attempt.finished_at is None:
            return
        category = (await self._repository.categories_of(profile.id)).get(attempt.specialization)
        if category is None:
            category = CandidateCategory(
                candidate_id=profile.id, specialization=attempt.specialization
            )
        category.grade = attempt.grade
        category.score = attempt.score or 0.0
        category.confirmed_at = attempt.finished_at
        category.change_allowed_at = attempt.finished_at + timedelta(days=attempt.grade_change_days)
        await self._repository.add(category)
        # The first confirmed category becomes the primary one; later ones wait for the
        # candidate's choice and only refresh the profile when they are the primary already.
        if (
            profile.assessment_status != AssessmentStatus.PASSED
            or profile.specialization == attempt.specialization
        ):
            _mirror(profile, category)

    async def _points(self, task: AssessmentTask, answer: AssessmentAnswer | None) -> float | None:
        """Share of the task earned, 0–1; None = waits for a reviewer."""
        if answer is None:
            return 0.0
        spec = spec_of(task)
        return await spec.grade(spec.payload(task), answer.answer, self._runner)

    # ── Variant ───────────────────────────────────────────────────────────────────────────

    async def _compose(
        self, test: AssessmentTest, specialization: str, seen: set[str]
    ) -> list[AssessmentTask]:
        composition = test_read(test).composition
        if isinstance(composition, FixedComposition):
            tasks = await self._repository.tasks_by_ids(composition.task_ids)
            return [
                tasks[task_id]
                for task_id in composition.task_ids
                if task_id in tasks and tasks[task_id].is_active
            ]
        return _draw(composition, await self._repository.platform_pool(), specialization, seen)

    # ── Guards and helpers ────────────────────────────────────────────────────────────────

    async def _profile(self, user: User) -> CandidateProfile:
        profile = await self._candidates.get_by_user(user.id)
        if profile is None:
            # Testing is the first step of the candidate path: the profile starts here.
            profile = await self._repository.add(
                CandidateProfile(user_id=user.id, display_name=user.email.split("@")[0])
            )
        return profile

    async def _attempt(self, user: User, attempt_id: uuid.UUID) -> AssessmentAttempt:
        attempt = await self._repository.get_attempt(attempt_id)
        profile = await self._candidates.get_by_user(user.id)
        if attempt is None or profile is None or attempt.candidate_id != profile.id:
            raise NotFoundError("Попытка не найдена")
        return attempt

    async def _running_attempt(self, user: User, attempt_id: uuid.UUID) -> AssessmentAttempt:
        attempt = await self._attempt(user, attempt_id)
        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise ConflictError("Тест уже завершён")
        if datetime.now(UTC) > _aware(attempt.expires_at):
            raise AttemptExpiredError()
        return attempt

    async def _tasks(self, attempt: AssessmentAttempt) -> list[AssessmentTask]:
        ids = [uuid.UUID(task_id) for task_id in attempt.task_ids]
        tasks = await self._repository.tasks_by_ids(ids)
        # A task deleted from the bank mid-attempt simply drops out of the variant.
        return [tasks[task_id] for task_id in ids if task_id in tasks]

    async def _task(self, attempt: AssessmentAttempt, task_id: uuid.UUID) -> AssessmentTask:
        task = await self._repository.get_task(task_id)
        if task is None or str(task_id) not in attempt.task_ids:
            raise NotFoundError("Задача не входит в этот тест")
        return task

    async def _settled_attempts(self, profile: CandidateProfile) -> Sequence[AssessmentAttempt]:
        """Attempts newest first; the ones abandoned past their deadline are closed on the way."""
        attempts = await self._repository.attempts_of(profile.id)
        now = datetime.now(UTC)
        for attempt in attempts:
            if not (
                attempt.status == AttemptStatus.IN_PROGRESS
                and now > _aware(attempt.expires_at) + ABANDON_AFTER
            ):
                continue
            if attempt.assignment_id is not None:
                await self.close_abandoned(attempt)
            else:
                attempt.status = AttemptStatus.EXPIRED
                attempt.finished_at = attempt.expires_at
                await self._repository.add(attempt)
                if profile.assessment_status != AssessmentStatus.PASSED:
                    profile.assessment_status = AssessmentStatus.FAILED
        return attempts

    def _retry_days(self, test: AssessmentTest) -> int:
        if test.retry_days is not None:
            return test.retry_days
        return self._settings.assessment_retry_days

    def _grade_change_days(self, test: AssessmentTest) -> int:
        if test.grade_change_days is not None:
            return test.grade_change_days
        return self._settings.assessment_grade_change_days

    def _detail(
        self,
        attempt: AssessmentAttempt,
        tasks: Sequence[AssessmentTask],
        answers: dict[uuid.UUID, AssessmentAnswer],
    ) -> AttemptDetail:
        return AttemptDetail(
            **_attempt_read(attempt).model_dump(),
            tasks=[_attempt_task(attempt, task, answers.get(task.id)) for task in tasks],
            runs_left=MAX_RUNS - attempt.runs_count,
            server_time=datetime.now(UTC),
        )


def _next_attempt_at(
    specialization: str,
    category: CandidateCategory | None,
    attempts: Sequence[AssessmentAttempt],
) -> datetime | None:
    """When a test of the specialization may start; None = right now.

    Every specialization keeps its own clock: a failure in one does not hold back another.
    `attempts` come newest first.
    """
    waits: list[datetime] = []
    last = next(
        (a for a in attempts if a.specialization == specialization and a.finished_at is not None),
        None,
    )
    if (
        last is not None
        and last.finished_at is not None
        and last.status in (AttemptStatus.FAILED, AttemptStatus.EXPIRED)
    ):
        waits.append(_aware(last.finished_at) + timedelta(days=last.retry_days))
    if category is not None:
        waits.append(_aware(category.change_allowed_at))
    allowed_at = max(waits, default=None)
    return allowed_at if allowed_at and allowed_at > datetime.now(UTC) else None


def _track(
    profile: CandidateProfile,
    specialization: str,
    category: CandidateCategory | None,
    attempts: Sequence[AssessmentAttempt],
) -> TrackRead:
    return TrackRead(
        specialization=specialization,
        status=AssessmentStatus.PASSED if category else AssessmentStatus.FAILED,
        grade=category.grade if category else None,
        score=category.score if category else None,
        next_attempt_at=_next_attempt_at(specialization, category, attempts),
        is_primary=category is not None
        and profile.assessment_status == AssessmentStatus.PASSED
        and profile.specialization == specialization,
    )


def _mirror(profile: CandidateProfile, category: CandidateCategory) -> None:
    """Copies the primary category into the profile, where search and feeds read it."""
    profile.specialization = category.specialization
    profile.grade = category.grade
    profile.assessment_score = category.score
    profile.grade_changed_at = category.confirmed_at
    profile.assessment_status = AssessmentStatus.PASSED


def _attempt_read(attempt: AssessmentAttempt) -> AttemptRead:
    return AttemptRead(
        id=attempt.id,
        assignment_id=attempt.assignment_id,
        title=attempt.title,
        specialization=attempt.specialization,
        grade=attempt.grade,
        status=attempt.status,
        score=attempt.score,
        pass_score=attempt.pass_score,
        started_at=_aware(attempt.started_at),
        expires_at=_aware(attempt.expires_at),
        finished_at=_aware(attempt.finished_at) if attempt.finished_at else None,
        breakdown=[TopicResult.model_validate(item) for item in attempt.breakdown]
        if attempt.breakdown is not None
        else None,
    )


def _attempt_task(
    attempt: AssessmentAttempt, task: AssessmentTask, answer: AssessmentAnswer | None
) -> AttemptTask:
    """Candidate view of a task: the kind decides what is safe to show."""
    spec = spec_of(task)
    payload = spec.payload(task)
    state = attempt.task_state.get(str(task.id))
    shown = spec.show_answer(payload, state, answer.answer) if answer else None
    return AttemptTask(
        id=task.id,
        kind=task.kind,
        topic=task.topic,
        difficulty=task.difficulty,
        title=task.title,
        statement=task.statement,
        content=spec.content(payload, state).model_dump(mode="json", by_alias=True),
        answer=shown.model_dump(mode="json", by_alias=True) if shown else None,
    )


def settle(
    attempt: AssessmentAttempt, tasks: Sequence[AssessmentTask], points: dict[uuid.UUID, float]
) -> None:
    """Final score, per-topic breakdown and the verdict, once every task has its points."""
    attempt.score = _score(tasks, points, attempt.quiz_weight)
    attempt.breakdown = [item.model_dump(mode="json") for item in _breakdown(tasks, points)]
    attempt.status = (
        AttemptStatus.PASSED if attempt.score >= attempt.pass_score else AttemptStatus.FAILED
    )


def _draw(
    composition: RulesComposition,
    pool: Sequence[AssessmentTask],
    specialization: str,
    seen: set[str],
) -> list[AssessmentTask]:
    """Random variant by the rules. Tasks the candidate has not met yet go first; when a narrow
    pool runs short, the rule widens (any scope, then any difficulty) instead of failing."""
    chosen: dict[uuid.UUID, AssessmentTask] = {}

    def fits_scope(task: AssessmentTask, scope: str) -> bool:
        if scope == "specialization":
            return specialization in task.specializations
        if scope == "general":
            return not task.specializations
        return not task.specializations or specialization in task.specializations

    for rule in composition.rules:
        left = rule.count
        for scope, strict in ((rule.scope, True), ("any", True), ("any", False)):
            if left == 0:
                break
            matching = [
                task
                for task in pool
                if task.id not in chosen
                and task.kind == rule.kind
                and (not rule.topics or task.topic in rule.topics)
                and (not strict or not rule.difficulty or task.difficulty in rule.difficulty)
                and fits_scope(task, scope)
            ]
            _random.shuffle(matching)
            matching.sort(key=lambda task: str(task.id) in seen)
            for task in matching[:left]:
                chosen[task.id] = task
            left -= min(left, len(matching))
    return list(chosen.values())


def _score(
    tasks: Sequence[AssessmentTask], points: dict[uuid.UUID, float], quiz_weight: int
) -> float:
    """0–100. Code tasks share `100 - quiz_weight`, every other kind shares `quiz_weight`;
    a test without one of the groups gives the other the whole weight."""
    code = [points.get(task.id, 0.0) for task in tasks if REGISTRY[task.kind].code_group]
    rest = [points.get(task.id, 0.0) for task in tasks if not REGISTRY[task.kind].code_group]
    if rest and code:
        share = quiz_weight / 100
        value = share * sum(rest) / len(rest) + (1 - share) * sum(code) / len(code)
    else:
        only = rest or code or [0.0]
        value = sum(only) / len(only)
    return round(value * 100, 1)


def _breakdown(
    tasks: Sequence[AssessmentTask], points: dict[uuid.UUID, float]
) -> list[TopicResult]:
    groups: dict[tuple[TaskKind, str], list[float]] = defaultdict(list)
    for task in tasks:
        groups[(task.kind, task.topic)].append(points.get(task.id, 0.0))
    return [
        TopicResult(
            topic=topic, kind=kind, earned=round(sum(values) / len(values), 2), total=len(values)
        )
        for (kind, topic), values in groups.items()
    ]
