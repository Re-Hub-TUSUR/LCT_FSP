"""Platform analytics: candidate and employer funnels, demand and supply by category.

Funnels are cohorts: accounts registered in the period and how far each of them got, ever.
The platform has no invitation flow yet (`/invitations` answers 501), so an «invitation» is any
way an employer reaches out today: an invitation row, a like on the candidate, a test sent.
«Accepted» is an accepted invitation or a conversation, which opens on mutual interest.
"""

from collections import Counter
from datetime import datetime
from typing import Any, Final

from sqlalchemy import (
    ColumnElement,
    Select,
    and_,
    case,
    exists,
    func,
    literal,
    or_,
    select,
    union_all,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.analytics.metrics import share
from app.models import (
    AssessmentAttempt,
    AttemptStatus,
    CandidateCategory,
    CandidateProfile,
    CandidateReaction,
    Company,
    Conversation,
    Grade,
    Invitation,
    InvitationStatus,
    ReactionKind,
    TestAssignment,
    User,
    UserRole,
    Vacancy,
)
from app.services.categories import GRADE_LABELS, SPECIALIZATIONS
from app.services.matching import as_utc


def _flag(condition: ColumnElement[bool]) -> ColumnElement[int]:
    return func.sum(case((condition, 1), else_=0))


def _since(column: Any, since: datetime | None) -> ColumnElement[bool]:
    return column >= since if since is not None else literal(True)


def _steps(names: list[tuple[str, str]], counts: list[int | None]) -> list[dict[str, Any]]:
    first = counts[0] or 0
    steps = []
    previous: int | None = first
    for (code, label), count in zip(names, counts, strict=True):
        steps.append(
            {
                "step": code,
                "label": label,
                "count": count,
                # Conversion from the first step and from the previous one.
                "fromStartShare": share(count, first) if count is not None else None,
                "fromPreviousShare": share(count, previous) if count is not None else None,
            }
        )
        if count is not None:
            previous = count
    return steps


async def candidate_funnel(session: AsyncSession, since: datetime | None) -> list[dict[str, Any]]:
    profile = CandidateProfile
    own_profile = and_(profile.user_id == User.id)
    grade_attempt = and_(
        AssessmentAttempt.candidate_id == profile.id, AssessmentAttempt.assignment_id.is_(None)
    )
    started = exists().where(own_profile, grade_attempt)
    finished = exists().where(
        own_profile,
        grade_attempt,
        AssessmentAttempt.status.in_((AttemptStatus.PASSED, AttemptStatus.FAILED)),
    )
    graded = exists().where(own_profile, CandidateCategory.candidate_id == profile.id)
    invited = or_(
        exists().where(own_profile, Invitation.candidate_id == profile.id),
        exists().where(
            own_profile,
            CandidateReaction.candidate_id == profile.id,
            CandidateReaction.kind == ReactionKind.LIKE,
        ),
        exists().where(own_profile, TestAssignment.candidate_id == profile.id),
    )
    accepted = or_(
        exists().where(
            own_profile,
            Invitation.candidate_id == profile.id,
            Invitation.status == InvitationStatus.ACCEPTED,
        ),
        exists().where(own_profile, Conversation.candidate_id == profile.id),
    )
    row = (
        await session.execute(
            select(
                func.count(),
                _flag(started),
                _flag(finished),
                _flag(graded),
                _flag(invited),
                _flag(accepted),
            ).where(User.role == UserRole.CANDIDATE, _since(User.created_at, since))
        )
    ).one()
    names = [
        ("registered", "Регистрация"),
        ("started_test", "Начал тест"),
        ("finished_test", "Прошёл тест"),
        ("graded", "Получил грейд"),
        ("invited", "Получил приглашение"),
        ("accepted", "Принял"),
    ]
    return _steps(names, [int(value or 0) for value in row])


async def employer_funnel(session: AsyncSession, since: datetime | None) -> list[dict[str, Any]]:
    own_company = Company.owner_id == User.id
    created_need = exists().where(own_company, Vacancy.company_id == Company.id)
    reached_out = or_(
        exists().where(own_company, Invitation.company_id == Company.id),
        exists().where(
            CandidateReaction.user_id == User.id, CandidateReaction.kind == ReactionKind.LIKE
        ),
        exists().where(own_company, TestAssignment.company_id == Company.id),
    )
    got_acceptance = or_(
        exists().where(
            own_company,
            Invitation.company_id == Company.id,
            Invitation.status == InvitationStatus.ACCEPTED,
        ),
        exists().where(own_company, Conversation.company_id == Company.id),
    )
    row = (
        await session.execute(
            select(
                func.count(), _flag(created_need), _flag(reached_out), _flag(got_acceptance)
            ).where(User.role == UserRole.EMPLOYER, _since(User.created_at, since))
        )
    ).one()
    names = [
        ("registered", "Регистрация"),
        ("created_need", "Создал потребность"),
        ("invited", "Отправил приглашение"),
        ("got_acceptance", "Получил принятие"),
        # Vacancies have no «closed with a hire» state: nothing to count yet.
        ("hired", "Закрыл с наймом"),
    ]
    return _steps(names, [*(int(value or 0) for value in row), None])


def _invitations_by_category(since: datetime | None) -> Select[Any]:
    """Every way an employer reached out, attributed to the candidate's current category."""
    profile = CandidateProfile
    parts = [
        select(profile.specialization, profile.grade)
        .join(Invitation, Invitation.candidate_id == profile.id)
        .where(_since(Invitation.created_at, since)),
        select(profile.specialization, profile.grade)
        .join(CandidateReaction, CandidateReaction.candidate_id == profile.id)
        .where(
            CandidateReaction.kind == ReactionKind.LIKE, _since(CandidateReaction.created_at, since)
        ),
        select(profile.specialization, profile.grade)
        .join(TestAssignment, TestAssignment.candidate_id == profile.id)
        .where(_since(TestAssignment.created_at, since)),
    ]
    reached = union_all(*parts).subquery()
    return (
        select(reached.c.specialization, reached.c.grade, func.count().label("count"))
        .where(reached.c.specialization.is_not(None), reached.c.grade.is_not(None))
        .group_by(reached.c.specialization, reached.c.grade)
    )


async def demand(session: AsyncSession, since: datetime | None) -> list[dict[str, Any]]:
    """Per category: open vacancies, outreach to candidates and candidates available.

    `deficit` = (vacancies + invitations) per available candidate: high values are categories
    where candidates are short. Searches are not logged, so their count is unknown.
    """
    vacancies = (
        await session.execute(
            select(Vacancy.specialization, Vacancy.grade, func.count())
            .where(Vacancy.published_at.is_not(None), _since(Vacancy.published_at, since))
            .group_by(Vacancy.specialization, Vacancy.grade)
        )
    ).all()
    invitations = (await session.execute(_invitations_by_category(since))).all()
    candidates = (
        await session.execute(
            select(CandidateProfile.specialization, CandidateProfile.grade, func.count())
            .where(
                CandidateProfile.specialization.is_not(None),
                CandidateProfile.grade.is_not(None),
                CandidateProfile.is_visible_to_employers.is_(True),
            )
            .group_by(CandidateProfile.specialization, CandidateProfile.grade)
        )
    ).all()

    table: dict[tuple[str, str], dict[str, Any]] = {}

    def cell(specialization: str, grade: Any) -> dict[str, Any]:
        code = grade.value if hasattr(grade, "value") else str(grade)
        key = (specialization, code)
        if key not in table:
            table[key] = {
                "specialization": specialization,
                "specializationLabel": SPECIALIZATIONS.get(specialization, specialization),
                "grade": code,
                "gradeLabel": next(
                    (label for item, label in GRADE_LABELS.items() if item.value == code), code
                ),
                "searches": None,
                "vacancies": 0,
                "invitations": 0,
                "candidates": 0,
            }
        return table[key]

    for field, found in (
        ("vacancies", vacancies),
        ("invitations", invitations),
        ("candidates", candidates),
    ):
        for row in found:
            cell(str(row[0]), row[1])[field] = int(row[2])

    rows = list(table.values())
    for row in rows:
        wanted = row["vacancies"] + row["invitations"]
        row["demand"] = wanted
        row["deficit"] = round(wanted / row["candidates"], 2) if row["candidates"] else None
        row["shortage"] = (row["candidates"] == 0 and wanted > 0) or (
            row["deficit"] is not None and row["deficit"] > 1
        )
    rows.sort(key=lambda row: (-row["demand"], row["specialization"], row["grade"]))
    return rows


# How many of the most frequent shortages of the bank are listed.
SHORTAGES: Final = 20
_SETTLED: Final = (AttemptStatus.PASSED, AttemptStatus.FAILED, AttemptStatus.EXPIRED)


async def grade_tests(session: AsyncSession, since: datetime | None) -> dict[str, Any]:
    """Platform grade tests started in the period, per grade: how many were started, settled
    and passed, and how often the bank ran short of tasks for the template (`draw_notes`).

    A «step up» is a test of a grade above the one the candidate had already confirmed in that
    specialization. The grade a candidate claims is stored nowhere, so this is the closest
    reading of «passed a grade above their own»: a test that tells grades apart lets few of
    them through, apart from honest growth."""
    rows = (
        await session.execute(
            select(
                AssessmentAttempt.candidate_id,
                AssessmentAttempt.specialization,
                AssessmentAttempt.grade,
                AssessmentAttempt.status,
                AssessmentAttempt.started_at,
                AssessmentAttempt.draw_notes,
            )
            .where(AssessmentAttempt.assignment_id.is_(None), AssessmentAttempt.grade.is_not(None))
            .order_by(AssessmentAttempt.started_at, AssessmentAttempt.id)
        )
    ).all()
    counts: dict[str, Counter[str]] = {grade.value: Counter() for grade in Grade}
    shortages: Counter[str] = Counter()
    # (candidate, specialization) → rank of the highest grade passed so far.
    confirmed: dict[tuple[Any, str | None], int] = {}
    for candidate_id, specialization, grade, status, started_at, notes in rows:
        if grade is None:
            continue
        track = (candidate_id, specialization)
        held = confirmed.get(track)
        if status == AttemptStatus.PASSED:
            confirmed[track] = max(grade.rank, held if held is not None else grade.rank)
        if since is not None and as_utc(started_at) < since:
            continue
        count = counts[grade.value]
        count["started"] += 1
        count["settled"] += status in _SETTLED
        count["passed"] += status == AttemptStatus.PASSED
        count["widened"] += bool(notes)
        if held is not None and grade.rank > held and status in _SETTLED:
            count["step_up"] += 1
            count["step_up_passed"] += status == AttemptStatus.PASSED
        shortages.update(notes or [])
    return {
        "grades": [
            {
                "grade": grade.value,
                "gradeLabel": label,
                "started": counts[grade.value]["started"],
                "settled": counts[grade.value]["settled"],
                "passed": counts[grade.value]["passed"],
                # Of the settled ones: a test still running or waiting for a check is not a fail.
                "passShare": share(counts[grade.value]["passed"], counts[grade.value]["settled"]),
                "widened": counts[grade.value]["widened"],
                "stepUp": counts[grade.value]["step_up"],
                "stepUpPassed": counts[grade.value]["step_up_passed"],
                "stepUpPassShare": share(
                    counts[grade.value]["step_up_passed"], counts[grade.value]["step_up"]
                ),
            }
            for grade, label in GRADE_LABELS.items()
        ],
        "shortages": [
            {"note": note, "count": count} for note, count in shortages.most_common(SHORTAGES)
        ],
    }


async def compute_platform(session: AsyncSession, since: datetime | None) -> dict[str, Any]:
    return {
        "candidateFunnel": await candidate_funnel(session, since),
        "employerFunnel": await employer_funnel(session, since),
        "demand": await demand(session, since),
        "gradeTests": await grade_tests(session, since),
        "missing": [
            "Заявленный кандидатом грейд не хранится: вместо него в таблице тестов считается "
            "сдача грейда выше уже подтверждённого.",
            "Посещаемость сайта: события посещений не записываются (раздел отключён).",
            "Число поисков по категориям: поисковые запросы не логируются.",
            "Найм: у вакансий нет статуса «закрыта с наймом».",
        ],
    }
