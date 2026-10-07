"""Platform analytics: candidate and employer funnels, demand and supply by category.

Funnels are cohorts: accounts registered in the period and how far each of them got, ever.
The platform has no invitation flow yet (`/invitations` answers 501), so an «invitation» is any
way an employer reaches out today: an invitation row, a like on the candidate, a test sent.
«Accepted» is an accepted invitation or a conversation, which opens on mutual interest.
"""

from datetime import datetime
from typing import Any

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
    Invitation,
    InvitationStatus,
    ReactionKind,
    TestAssignment,
    User,
    UserRole,
    Vacancy,
)
from app.services.categories import GRADE_LABELS, SPECIALIZATIONS


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


async def compute_platform(session: AsyncSession, since: datetime | None) -> dict[str, Any]:
    return {
        "candidateFunnel": await candidate_funnel(session, since),
        "employerFunnel": await employer_funnel(session, since),
        "demand": await demand(session, since),
        "missing": [
            "Посещаемость сайта: события посещений не записываются (раздел отключён).",
            "Число поисков по категориям: поисковые запросы не логируются.",
            "Найм: у вакансий нет статуса «закрыта с наймом».",
        ],
    }
