"""Analytics screens. GET returns the latest stored snapshot; only POST …/recalculate computes."""

import uuid
from collections.abc import Callable, Iterable, Sequence
from typing import Annotated, Any, Final

from fastapi import APIRouter, Query, Response
from sqlalchemy import select

from app.admin.activity import merge_employer_rows
from app.admin.analytics.metrics import TaskFlag
from app.admin.csv_export import csv_response
from app.admin.dependencies import SnapshotsDep
from app.admin.enums import AnalyticsPeriod, TaskStatus
from app.admin.models import AdminTaskMeta
from app.admin.schemas import (
    AnalyticsFilters,
    Block,
    EmployerSignalsPage,
    SnapshotRead,
    TaskAnalyticsPage,
)
from app.admin.services.snapshots import meta
from app.admin.tasks_status import STATUS_LABELS, status_of
from app.core.errors import NotFoundError
from app.dependencies.auth import AdminUser
from app.dependencies.common import SessionDep
from app.models import AssessmentTask

router = APIRouter(prefix="/analytics")

PER_PAGE: Final = 50
Period = Annotated[AnalyticsPeriod, Query()]
TaskId = Annotated[uuid.UUID | None, Query(alias="taskId")]

FLAG_LABELS: Final = {
    TaskFlag.OUT_OF_TARGET.value: "Вне целевой сложности",
    TaskFlag.VARIANT_SPREAD.value: "Разброс вариантов",
    TaskFlag.POSSIBLE_LEAK.value: "Возможная утечка",
}
SIGNAL_LABELS: Final = {
    "invites_spike": "Аномально много приглашений за сутки",
    "low_response": "Низкая доля ответов кандидатам",
    "reaction_flapping": "Частая смена отметки одного кандидата",
    "requisites_churn": "Частая смена реквизитов",
    "junk_vacancies": "Вакансии без слов",
    "meeting_churn": "Частые отмены встреч",
    "chat_media_spam": "Много файлов в чате",
    "invalid_industry": "Направление не из списка",
}


def _live_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "companies": len(rows),
        "flagged": sum(1 for row in rows if row["signals"]),
        "invitesSpike": sum(1 for row in rows if "invites_spike" in row["signals"]),
        "lowResponse": sum(1 for row in rows if "low_response" in row["signals"]),
        "medianInvitesPerDay": None,
    }


def _paged(items: list[dict[str, Any]], page: int) -> tuple[list[dict[str, Any]], int, int]:
    total = len(items)
    start = (page - 1) * PER_PAGE
    return items[start : start + PER_PAGE], total, -(-total // PER_PAGE)


def _task_rows(
    rows: list[dict[str, Any]],
    *,
    flag: str | None,
    q: str | None,
    specialization: str | None,
    kind: str | None,
) -> list[dict[str, Any]]:
    result = rows
    if flag == "any":
        result = [row for row in result if row["flags"]]
    elif flag:
        result = [row for row in result if flag in row["flags"]]
    if q:
        needle = q.strip().lower()
        result = [row for row in result if needle in row["title"].lower()]
    if specialization:
        result = [row for row in result if specialization in row["specializations"]]
    if kind:
        result = [row for row in result if row["kind"] == kind]
    return result


@router.get("/tasks", summary="Task analytics table from the latest snapshot")
async def task_table(
    *,
    _: AdminUser,
    snapshots: SnapshotsDep,
    session: SessionDep,
    period: Period = AnalyticsPeriod.QUARTER,
    page: Annotated[int, Query(ge=1)] = 1,
    flag: Annotated[str | None, Query(max_length=32)] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
    specialization: Annotated[str | None, Query(max_length=64)] = None,
    kind: Annotated[str | None, Query(max_length=16)] = None,
) -> TaskAnalyticsPage:
    snapshot = await snapshots.latest("tasks", AnalyticsFilters(period=period))
    if snapshot is None:
        return TaskAnalyticsPage(
            snapshot=None,
            summary=None,
            rules=None,
            items=[],
            total=0,
            page=page,
            per_page=PER_PAGE,
            pages=0,
        )
    rows = _task_rows(
        snapshot.result["tasks"], flag=flag, q=q, specialization=specialization, kind=kind
    )
    items, total, pages = _paged(rows, page)
    # The status may have changed since the calculation (e.g. «marked as leaked»).
    ids = [uuid.UUID(item["taskId"]) for item in items]
    live = (
        {
            str(task.id): status_of(task, task_meta).value
            for task, task_meta in (
                await session.execute(
                    select(AssessmentTask, AdminTaskMeta)
                    .outerjoin(AdminTaskMeta, AdminTaskMeta.task_id == AssessmentTask.id)
                    .where(AssessmentTask.id.in_(ids))
                )
            ).all()
        }
        if ids
        else {}
    )
    items = [{**item, "status": live.get(item["taskId"], item["status"])} for item in items]
    return TaskAnalyticsPage(
        snapshot=meta(snapshot),
        summary=snapshot.result["summary"],
        rules=snapshot.result["rules"],
        items=items,
        total=total,
        page=page,
        per_page=PER_PAGE,
        pages=pages,
    )


@router.get("/employers", summary="Companies with signals, from the latest snapshot")
async def employer_table(
    *,
    _: AdminUser,
    snapshots: SnapshotsDep,
    session: SessionDep,
    period: Period = AnalyticsPeriod.QUARTER,
    page: Annotated[int, Query(ge=1)] = 1,
    signal: Annotated[str | None, Query(max_length=32)] = None,
    case_status: Annotated[str | None, Query(alias="status", max_length=16)] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
) -> EmployerSignalsPage:
    snapshot = await snapshots.latest("employers", AnalyticsFilters(period=period))
    rows = await merge_employer_rows(
        session, snapshot.result["companies"] if snapshot else None
    )
    if snapshot is None and not rows:
        return EmployerSignalsPage(
            snapshot=None,
            summary=None,
            unavailable=[],
            items=[],
            total=0,
            page=page,
            per_page=PER_PAGE,
            pages=0,
        )
    if signal == "any":
        rows = [row for row in rows if row["signals"]]
    elif signal:
        rows = [row for row in rows if signal in row["signals"]]
    if case_status:
        rows = [row for row in rows if row["caseStatus"] == case_status]
    if q:
        needle = q.strip().lower()
        rows = [row for row in rows if needle in row["name"].lower()]
    items, total, pages = _paged(rows, page)
    summary = snapshot.result["summary"] if snapshot else _live_summary(rows)
    unavailable = snapshot.result.get("unavailable", []) if snapshot else []
    return EmployerSignalsPage(
        snapshot=meta(snapshot) if snapshot else None,
        summary=summary,
        unavailable=unavailable,
        items=items,
        total=total,
        page=page,
        per_page=PER_PAGE,
        pages=pages,
    )


@router.get("/snapshot/{block}", summary="The latest snapshot of a block (platform, task card)")
async def latest_snapshot(
    block: Block,
    _: AdminUser,
    snapshots: SnapshotsDep,
    period: Period = AnalyticsPeriod.QUARTER,
    task_id: TaskId = None,
) -> SnapshotRead:
    snapshot = await snapshots.latest(block, AnalyticsFilters(period=period, task_id=task_id))
    if snapshot is None:
        return SnapshotRead(snapshot=None, result=None)
    return SnapshotRead(snapshot=meta(snapshot), result=snapshot.result)


@router.post(
    "/{block}/recalculate",
    summary="Compute the block now and store the snapshot",
    description="At most once in 5 minutes for the same filters (429 with `nextAllowedAt`); "
    "a second request while one is running gets 409.",
)
async def recalculate(
    block: Block, user: AdminUser, filters: AnalyticsFilters, snapshots: SnapshotsDep
) -> SnapshotRead:
    snapshot = await snapshots.recalculate(block, filters, user)
    return SnapshotRead(snapshot=meta(snapshot), result=snapshot.result)


# ── CSV of a stored snapshot ──────────────────────────────────────────────────────────────────

METRIC_HEADERS: Final = [
    "Попыток",
    "Решили полностью, %",
    "Решили частично, %",
    "Бросили, %",
    "Не решили, %",
    "Среднее время, с",
    "Медиана времени, с",
]


def _metrics(row: dict[str, Any]) -> list[Any]:
    return [
        row.get("attempts"),
        row.get("fullShare"),
        row.get("partialShare"),
        row.get("abandonedShare"),
        row.get("unsolvedShare"),
        row.get("avgTimeSec"),
        row.get("medianTimeSec"),
    ]


type Table = tuple[Sequence[str], Callable[[dict[str, Any]], Iterable[list[Any]]]]


def _grouped(key: str, label: str, table: str) -> Table:
    return (
        [label, *METRIC_HEADERS],
        lambda result: ([row.get(key), *_metrics(row)] for row in result.get(table, [])),
    )


def _funnel(table: str) -> Table:
    return (
        ["Шаг", "Количество", "От первого шага, %", "От предыдущего, %"],
        lambda result: (
            [row["label"], row["count"], row["fromStartShare"], row["fromPreviousShare"]]
            for row in result.get(table, [])
        ),
    )


TABLES: Final[dict[str, dict[str, Table]]] = {
    "tasks": {
        "tasks": (
            [
                "ID",
                "Название",
                "Тип",
                "Специализации",
                "Грейд",
                "Навык",
                "Статус",
                *METRIC_HEADERS,
                "Разброс вариантов, п.п.",
                "Макс. рост за неделю, п.п.",
                "Флаги",
            ],
            lambda result: (
                [
                    row["taskId"],
                    row["title"],
                    row["kind"],
                    row["specializations"],
                    row["grade"],
                    row["skill"],
                    STATUS_LABELS[TaskStatus(row["status"])],
                    *_metrics(row),
                    row["variantSpreadPp"],
                    row["maxWeeklyJumpPp"],
                    [FLAG_LABELS.get(flag, flag) for flag in row["flags"]],
                ]
                for row in result["tasks"]
            ),
        )
    },
    "task_card": {
        "variants": _grouped("variant", "Вариант", "variants"),
        "grades": _grouped("grade", "Заявленный грейд", "grades"),
        "weekly": _grouped("week", "Неделя", "weekly"),
        "monthly": _grouped("month", "Месяц", "monthly"),
        "histogram": (
            ["Минута", "Попыток"],
            lambda result: ([row["minute"], row["count"]] for row in result.get("histogram", [])),
        ),
    },
    "platform": {
        "candidate_funnel": _funnel("candidateFunnel"),
        "employer_funnel": _funnel("employerFunnel"),
        "demand": (
            [
                "Специализация",
                "Грейд",
                "Поисков",
                "Вакансий",
                "Приглашений",
                "Кандидатов",
                "Спрос на кандидата",
                "Не хватает кандидатов",
            ],
            lambda result: (
                [
                    row["specializationLabel"],
                    row["gradeLabel"],
                    row["searches"],
                    row["vacancies"],
                    row["invitations"],
                    row["candidates"],
                    row["deficit"],
                    row["shortage"],
                ]
                for row in result.get("demand", [])
            ),
        ),
    },
    "employers": {
        "companies": (
            [
                "ID",
                "Компания",
                "Сигналы",
                "Приглашений всего",
                "Макс. приглашений за сутки",
                "Медиана работодателей за сутки",
                "Откликов кандидатов",
                "Ответов",
                "Доля ответов, %",
            ],
            lambda result: (
                [
                    row["companyId"],
                    row["name"],
                    [SIGNAL_LABELS.get(signal, signal) for signal in row["signals"]],
                    row["invitesTotal"],
                    row["invitesMaxPerDay"],
                    row["invitesMedianPerDay"],
                    row["inbound"],
                    row["answered"],
                    row["responseShare"],
                ]
                for row in result.get("companies", [])
            ),
        )
    },
}


@router.get(
    "/{block}/export.csv",
    summary="A table of the latest snapshot as CSV",
    description="Reads the stored snapshot: exporting never recalculates.",
)
async def export_snapshot(
    block: Block,
    _: AdminUser,
    snapshots: SnapshotsDep,
    table: Annotated[str, Query(max_length=32)],
    period: Period = AnalyticsPeriod.QUARTER,
    task_id: TaskId = None,
) -> Response:
    spec = TABLES[block].get(table)
    if spec is None:
        raise NotFoundError("Такой таблицы в этом блоке нет")
    snapshot = await snapshots.latest(block, AnalyticsFilters(period=period, task_id=task_id))
    if snapshot is None:
        raise NotFoundError("Нет сохранённого расчёта: нажмите «Пересчитать»")
    headers, rows = spec
    stamp = meta(snapshot).computed_at.strftime("%Y%m%d-%H%M")
    return csv_response(
        f"{block}-{table}-{period.value}-{stamp}.csv", headers, rows(snapshot.result)
    )
