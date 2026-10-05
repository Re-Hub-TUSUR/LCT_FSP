"""Candidate side of testing: draw a variant, collect answers, run code, score, set the category.

Open test groups serve "Run"; hidden ones are executed only on finish. Correct quiz options and
hidden groups never leave this module.
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
    AttemptStatus,
    CandidateProfile,
    TaskKind,
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
    CodeAnswer,
    FixedComposition,
    LanguageOption,
    RulesComposition,
    RunRequest,
    RunResponse,
    RunResult,
    SampleTest,
    TopicResult,
)
from app.services.assessment_bank import (
    allowed_languages,
    code_payload,
    judge,
    quiz_payload,
    test_read,
)
from app.services.categories import SPECIALIZATIONS, category_for
from app.services.code_runner import COMPILERS, CodeRunner

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
                active_attempt_id=None,
                next_attempt_at=None,
                code_runner_available=self._runner.available,
                history=[],
            )
        attempts = await self._settled_attempts(profile)
        active = next((a for a in attempts if a.status == AttemptStatus.IN_PROGRESS), None)
        confirmed = profile.assessment_status == AssessmentStatus.PASSED
        return AssessmentStatusRead(
            status=profile.assessment_status,
            specialization=profile.specialization if confirmed else None,
            grade=profile.grade if confirmed else None,
            score=profile.assessment_score,
            active_attempt_id=active.id if active else None,
            next_attempt_at=self._next_attempt_at(profile, attempts),
            code_runner_available=self._runner.available,
            history=[_attempt_read(attempt) for attempt in attempts],
        )

    async def start(self, user: User, data: AttemptStart) -> AttemptDetail:
        if data.specialization not in SPECIALIZATIONS:
            raise AppError("Неизвестная специализация")
        profile = await self._profile(user)
        attempts = await self._settled_attempts(profile)
        if any(attempt.status == AttemptStatus.IN_PROGRESS for attempt in attempts):
            raise ConflictError("У вас уже есть незавершённый тест")
        allowed_at = self._next_attempt_at(profile, attempts)
        if allowed_at is not None:
            raise ConflictError(
                "Повторная попытка пока недоступна", details={"nextAttemptAt": allowed_at}
            )
        test = await self._repository.platform_test(data.grade)
        if test is None:
            raise ConflictError("Тест для этого грейда ещё не подготовлен")

        seen = {task_id for attempt in attempts for task_id in attempt.task_ids}
        tasks = await self._compose(test, data.specialization, seen)
        if not tasks:
            raise ConflictError("Банк задач для этой специализации пока пуст")

        category = category_for(data.specialization, data.grade)
        now = datetime.now(UTC)
        attempt = await self._repository.add(
            AssessmentAttempt(
                candidate_id=profile.id,
                test_id=test.id,
                title=category.label if category else test.title,
                specialization=data.specialization,
                grade=data.grade,
                status=AttemptStatus.IN_PROGRESS,
                pass_score=test.pass_score,
                quiz_weight=test.quiz_weight,
                started_at=now,
                expires_at=now + timedelta(minutes=test.duration_minutes),
                task_ids=[str(task.id) for task in tasks],
                option_orders={
                    str(task.id): _random.sample(
                        range(len(quiz_payload(task).options)), len(quiz_payload(task).options)
                    )
                    for task in tasks
                    if task.kind == TaskKind.QUIZ
                },
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
        if task.kind == TaskKind.QUIZ:
            order = attempt.option_orders[str(task.id)]
            selected = list(dict.fromkeys(data.selected or []))
            if any(not 0 <= position < len(order) for position in selected) or (
                len(selected) > 1 and not quiz_payload(task).multiple
            ):
                raise AppError("Некорректный вариант ответа")
            value: dict[str, object] = {"selected": sorted(order[pos] for pos in selected)}
        else:
            if data.language is None or data.code is None:
                raise AppError("Передайте язык и код решения")
            self._check_language(task, data.language)
            value = {"language": data.language, "code": data.code}

        saved = (await self._repository.answers_of(attempt.id)).get(task.id)
        if saved is None:
            saved = AssessmentAnswer(attempt_id=attempt.id, task_id=task.id)
        saved.answer = value
        await self._repository.add(saved)

    async def run(self, user: User, attempt_id: uuid.UUID, data: RunRequest) -> RunResponse:
        attempt = await self._running_attempt(user, attempt_id)
        task = await self._task(attempt, data.task_id)
        if task.kind != TaskKind.CODE:
            raise AppError("Запуск доступен только для задач на код")
        self._check_language(task, data.language)

        now = datetime.now(UTC)
        if attempt.runs_count >= MAX_RUNS:
            raise TooManyRequestsError("Лимит запусков в этом тесте исчерпан")
        if attempt.last_run_at and now - _aware(attempt.last_run_at) < RUN_INTERVAL:
            raise TooManyRequestsError("Запускать код можно раз в несколько секунд")
        attempt.runs_count += 1
        attempt.last_run_at = now
        await self._repository.add(attempt)

        payload = code_payload(task)
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
        tasks = await self._tasks(attempt)
        answers = await self._repository.answers_of(attempt.id)

        points = dict(
            zip(
                (task.id for task in tasks),
                await asyncio.gather(*(self._points(task, answers.get(task.id)) for task in tasks)),
                strict=True,
            )
        )
        for task_id, answer in answers.items():
            answer.points = points.get(task_id, 0.0)
            await self._repository.add(answer)

        attempt.score = _score(tasks, points, attempt.quiz_weight)
        attempt.breakdown = [item.model_dump(mode="json") for item in _breakdown(tasks, points)]
        passed = attempt.score >= attempt.pass_score
        attempt.status = AttemptStatus.PASSED if passed else AttemptStatus.FAILED
        attempt.finished_at = datetime.now(UTC)
        await self._repository.add(attempt)

        profile = await self._candidates.get(attempt.candidate_id)
        if profile is not None and attempt.grade is not None:
            if passed:
                profile.specialization = attempt.specialization
                profile.grade = attempt.grade
                profile.assessment_score = attempt.score
                profile.grade_changed_at = attempt.finished_at
                profile.assessment_status = AssessmentStatus.PASSED
            elif profile.assessment_status != AssessmentStatus.PASSED:
                # A failed test assigns nothing; an earlier confirmed category stays as it was.
                profile.assessment_status = AssessmentStatus.FAILED
        return _attempt_read(attempt)

    async def _points(self, task: AssessmentTask, answer: AssessmentAnswer | None) -> float:
        """Share of the task earned, 0–1."""
        if answer is None:
            return 0.0
        if task.kind == TaskKind.QUIZ:
            return float(
                sorted(answer.answer.get("selected", [])) == sorted(quiz_payload(task).correct)
            )
        payload = code_payload(task)
        hidden = [group for group in payload.groups if group.hidden]
        executions = await asyncio.gather(
            *(
                self._runner.run(
                    compiler=answer.answer["language"],
                    code=answer.answer["code"],
                    stdin=group.input,
                )
                for group in hidden
            )
        )
        passed = sum(
            judge(execution, group.expected, payload.time_limit) == "ok"
            for group, execution in zip(hidden, executions, strict=True)
        )
        return passed / len(hidden)

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

    @staticmethod
    def _check_language(task: AssessmentTask, language: str) -> None:
        if language not in allowed_languages(code_payload(task)):
            raise AppError("Этот язык недоступен для задачи")

    async def _settled_attempts(self, profile: CandidateProfile) -> Sequence[AssessmentAttempt]:
        """Attempts newest first; the ones abandoned past their deadline are closed on the way."""
        attempts = await self._repository.attempts_of(profile.id)
        now = datetime.now(UTC)
        for attempt in attempts:
            if (
                attempt.status == AttemptStatus.IN_PROGRESS
                and now > _aware(attempt.expires_at) + ABANDON_AFTER
            ):
                attempt.status = AttemptStatus.EXPIRED
                attempt.finished_at = attempt.expires_at
                await self._repository.add(attempt)
                if profile.assessment_status != AssessmentStatus.PASSED:
                    profile.assessment_status = AssessmentStatus.FAILED
        return attempts

    def _next_attempt_at(
        self, profile: CandidateProfile, attempts: Sequence[AssessmentAttempt]
    ) -> datetime | None:
        """When the next attempt may start; None = right now."""
        waits: list[datetime] = []
        finished = [attempt for attempt in attempts if attempt.finished_at is not None]
        if finished and finished[0].status in (AttemptStatus.FAILED, AttemptStatus.EXPIRED):
            last = finished[0].finished_at
            if last is not None:
                waits.append(_aware(last) + timedelta(days=self._settings.assessment_retry_days))
        if profile.assessment_status == AssessmentStatus.PASSED and profile.grade_changed_at:
            waits.append(
                _aware(profile.grade_changed_at)
                + timedelta(days=self._settings.assessment_grade_change_days)
            )
        allowed_at = max(waits, default=None)
        return allowed_at if allowed_at and allowed_at > datetime.now(UTC) else None

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


def _attempt_read(attempt: AssessmentAttempt) -> AttemptRead:
    return AttemptRead(
        id=attempt.id,
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
    """Candidate view of a task: no correct options, no hidden groups, no reference solution."""
    common = {
        "id": task.id,
        "kind": task.kind,
        "topic": task.topic,
        "difficulty": task.difficulty,
        "title": task.title,
        "statement": task.statement,
    }
    if task.kind == TaskKind.QUIZ:
        quiz = quiz_payload(task)
        order = attempt.option_orders[str(task.id)]
        chosen = set(answer.answer.get("selected", [])) if answer else set()
        return AttemptTask(
            **common,
            options=[quiz.options[index] for index in order],
            multiple=quiz.multiple,
            selected=[position for position, index in enumerate(order) if index in chosen],
        )
    code = code_payload(task)
    return AttemptTask(
        **common,
        languages=[
            LanguageOption(id=language, label=COMPILERS[language])
            for language in allowed_languages(code)
        ],
        time_limit=code.time_limit,
        samples=[
            SampleTest(input=group.input, expected=group.expected)
            for group in code.groups
            if not group.hidden
        ],
        draft=CodeAnswer.model_validate(answer.answer) if answer else None,
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
    """0–100. A test of one kind only gives that kind the whole weight."""
    by_kind: dict[TaskKind, list[float]] = defaultdict(list)
    for task in tasks:
        by_kind[task.kind].append(points.get(task.id, 0.0))
    quiz, code = by_kind.get(TaskKind.QUIZ), by_kind.get(TaskKind.CODE)
    if quiz and code:
        share = quiz_weight / 100
        value = share * sum(quiz) / len(quiz) + (1 - share) * sum(code) / len(code)
    else:
        only = quiz or code or [0.0]
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
