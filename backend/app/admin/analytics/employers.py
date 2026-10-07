"""Signals that a company may be misusing the platform.

- invitations: the company's busiest day against the median busiest day of employers;
- responses: how many candidates who liked the company's vacancies heard back from it
  (a like back or a conversation);
- fictitious vacancies and complaints: the platform has neither a «closed with a hire» state of
  vacancies nor complaints, so these signals are reported as unavailable.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import case, exists, func, literal, or_, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.admin.analytics.metrics import invites_anomalous, response_low, share
from app.admin.analytics.sql import Dialect, medians
from app.models import (
    CandidateProfile,
    CandidateReaction,
    Company,
    Conversation,
    Invitation,
    ReactionKind,
    TestAssignment,
    Vacancy,
    VacancyReaction,
)


def _since(column: Any, since: datetime | None) -> Any:
    return column >= since if since is not None else literal(True)


async def compute_employers(
    session: AsyncSession, since: datetime | None, parameters: dict[str, int]
) -> dict[str, Any]:
    dialect = Dialect.of(session)

    # One row per outreach of a company to a candidate, with its day.
    outreach = union_all(
        select(
            Company.id.label("company_id"), dialect.day(CandidateReaction.created_at).label("day")
        )
        .join(CandidateReaction, CandidateReaction.user_id == Company.owner_id)
        .where(
            CandidateReaction.kind == ReactionKind.LIKE,
            _since(CandidateReaction.created_at, since),
        ),
        select(Invitation.company_id, dialect.day(Invitation.created_at)).where(
            _since(Invitation.created_at, since)
        ),
        select(TestAssignment.company_id, dialect.day(TestAssignment.created_at)).where(
            _since(TestAssignment.created_at, since)
        ),
    ).subquery()
    per_day = (
        select(outreach.c.company_id, outreach.c.day, func.count().label("hits"))
        .group_by(outreach.c.company_id, outreach.c.day)
        .subquery()
    )
    busiest = (
        select(
            per_day.c.company_id,
            func.max(per_day.c.hits).label("max_per_day"),
            func.sum(per_day.c.hits).label("total"),
        )
        .group_by(per_day.c.company_id)
        .subquery()
    )
    invites = {
        row.company_id: (int(row.max_per_day), int(row.total))
        for row in (await session.execute(select(busiest))).all()
    }
    median_per_day = (await medians(session, dialect, busiest, "max_per_day", [])).get(())

    # Candidates who liked a vacancy of the company, and whether the company answered them.
    liker = aliased(CandidateProfile)
    pairs = (
        select(
            Company.id.label("company_id"),
            Company.owner_id.label("owner_id"),
            liker.id.label("candidate_id"),
        )
        .join(Vacancy, Vacancy.company_id == Company.id)
        .join(VacancyReaction, VacancyReaction.vacancy_id == Vacancy.id)
        .join(liker, liker.user_id == VacancyReaction.user_id)
        .where(
            VacancyReaction.kind == ReactionKind.LIKE,
            _since(VacancyReaction.created_at, since),
        )
        .distinct()
        .subquery()
    )
    answered = or_(
        exists().where(
            CandidateReaction.user_id == pairs.c.owner_id,
            CandidateReaction.candidate_id == pairs.c.candidate_id,
            CandidateReaction.kind == ReactionKind.LIKE,
        ),
        exists().where(
            Conversation.company_id == pairs.c.company_id,
            Conversation.candidate_id == pairs.c.candidate_id,
        ),
    )
    responses = {
        row.company_id: (int(row.inbound), int(row.answered or 0))
        for row in (
            await session.execute(
                select(
                    pairs.c.company_id,
                    func.count().label("inbound"),
                    func.sum(case((answered, 1), else_=0)).label("answered"),
                ).group_by(pairs.c.company_id)
            )
        ).all()
    }

    company_ids = set(invites) | set(responses)
    companies = (
        {
            company.id: company
            for company in (
                await session.scalars(select(Company).where(Company.id.in_(company_ids)))
            ).all()
        }
        if company_ids
        else {}
    )

    factor = parameters["invite_anomaly_factor"]
    minimum_daily = parameters["invite_anomaly_min"]
    rows: list[dict[str, Any]] = []
    for company_id, company in companies.items():
        max_per_day, total = invites.get(company_id, (0, 0))
        inbound_count, answered_count = responses.get(company_id, (0, 0))
        signals = []
        if invites_anomalous(max_per_day, median_per_day, factor, minimum_daily):
            signals.append("invites_spike")
        if response_low(
            inbound_count,
            answered_count,
            parameters["low_response_share"],
            parameters["low_response_min_inbound"],
        ):
            signals.append("low_response")
        rows.append(
            {
                "companyId": str(company_id),
                "name": company.name,
                "signals": signals,
                "invitesTotal": total,
                "invitesMaxPerDay": max_per_day,
                "invitesMedianPerDay": median_per_day,
                "inbound": inbound_count,
                "answered": answered_count,
                "responseShare": share(answered_count, inbound_count),
                # Not computable on the current data model.
                "fakeVacancyShare": None,
                "complaints": None,
            }
        )
    rows.sort(key=lambda row: (-len(row["signals"]), -row["invitesMaxPerDay"], row["name"]))
    return {
        "companies": rows,
        "summary": {
            "companies": len(rows),
            "flagged": sum(1 for row in rows if row["signals"]),
            "invitesSpike": sum(1 for row in rows if "invites_spike" in row["signals"]),
            "lowResponse": sum(1 for row in rows if "low_response" in row["signals"]),
            "medianInvitesPerDay": median_per_day,
        },
        "unavailable": [
            "Доля вакансий, закрытых без подтверждённого найма: у вакансий нет статуса закрытия.",
            "Жалобы кандидатов: в платформе нет сущности жалоб.",
        ],
    }


def company_signal_rows(result: dict[str, Any], company_id: uuid.UUID) -> dict[str, Any] | None:
    """The company's row of a stored employers snapshot."""
    key = str(company_id)
    return next((row for row in result.get("companies", []) if row["companyId"] == key), None)
