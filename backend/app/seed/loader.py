"""Writes the demo dataset into the database, replacing whatever an earlier run wrote."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentStatus,
    AssessmentTask,
    AssessmentTest,
    CandidateProfile,
    CandidateReaction,
    Company,
    EmailVerificationCode,
    FspAchievement,
    Invitation,
    User,
    UserRole,
    Vacancy,
    VacancyReaction,
)
from app.seed.fixtures import CandidateFixture, CompanyFixture, SeedData, VacancyFixture

# Demo accounts share one password. Override it on a public stand with SEED_USER_PASSWORD.
PASSWORD_ENV: Final = "SEED_USER_PASSWORD"  # noqa: S105 - variable name, not a secret
DEFAULT_PASSWORD: Final = "kadry-demo-2026"  # noqa: S105 - documented password of demo accounts

# Ids derive from fixture keys, so links to demo profiles survive re-seeding.
SEED_NAMESPACE: Final = uuid.UUID("6f1c8f8e-2b0b-4c51-9d8a-3f2a7c1e5b90")


def seed_id(kind: str, key: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, f"{kind}:{key}")


class SeedConflictError(Exception):
    """A demo email belongs to an account the seed did not create."""


@dataclass(frozen=True, slots=True)
class SeedSummary:
    companies: int
    vacancies: int
    candidates: int
    fsp_achievements: int


def _ago(now: datetime, days: int) -> datetime:
    return now - timedelta(days=days)


def _employer(company: CompanyFixture, password_hash: str, now: datetime) -> User:
    registered = _ago(now, company.registered_days_ago)
    return User(
        id=seed_id("user", company.key),
        email=company.owner_email,
        password_hash=password_hash,
        role=UserRole.EMPLOYER,
        is_email_verified=True,
        personal_data_consent=True,
        created_at=registered,
        updated_at=registered,
    )


def _company(company: CompanyFixture, now: datetime) -> Company:
    registered = _ago(now, company.registered_days_ago)
    return Company(
        id=seed_id("company", company.key),
        owner_id=seed_id("user", company.key),
        name=company.name,
        industry=company.industry,
        description=company.description,
        city=company.city,
        size=company.size,
        website=company.website,
        contact_email=company.contact_email,
        created_at=registered,
        updated_at=registered,
    )


def _vacancy(vacancy: VacancyFixture, order: int, now: datetime) -> Vacancy:
    published = None
    if vacancy.published_days_ago is not None:
        # Minutes keep vacancies published on the same day in a stable order.
        published = _ago(now, vacancy.published_days_ago) - timedelta(minutes=order)
    created = published or _ago(now, 1)
    return Vacancy(
        id=seed_id("vacancy", vacancy.key),
        company_id=seed_id("company", vacancy.company_key),
        title=vacancy.title,
        description=vacancy.description,
        specialization=vacancy.specialization,
        grade=vacancy.grade,
        stack=vacancy.stack,
        salary_from=vacancy.salary_from,
        salary_to=vacancy.salary_to,
        work_format=vacancy.work_format,
        city=vacancy.city,
        published_at=published,
        created_at=created,
        updated_at=created,
    )


def _candidate_user(candidate: CandidateFixture, password_hash: str, now: datetime) -> User:
    registered = _ago(now, candidate.registered_days_ago)
    return User(
        id=seed_id("user", candidate.key),
        email=candidate.email,
        password_hash=password_hash,
        role=UserRole.CANDIDATE,
        is_email_verified=True,
        personal_data_consent=True,
        created_at=registered,
        updated_at=registered,
    )


def _candidate(candidate: CandidateFixture, now: datetime) -> CandidateProfile:
    registered = _ago(now, candidate.registered_days_ago)
    assessed = (
        None if candidate.assessed_days_ago is None else _ago(now, candidate.assessed_days_ago)
    )
    return CandidateProfile(
        id=seed_id("candidate", candidate.key),
        user_id=seed_id("user", candidate.key),
        display_name=candidate.display_name,
        headline=candidate.headline,
        about=candidate.about,
        stack=candidate.stack,
        soft_skills=candidate.soft_skills,
        experience_years=candidate.experience_years,
        english_level=candidate.english_level,
        city=candidate.city,
        relocation_ready=candidate.relocation_ready,
        work_formats=[work_format.value for work_format in candidate.work_formats],
        salary_expectation=candidate.salary_expectation,
        specialization=candidate.specialization,
        grade=candidate.grade,
        assessment_score=candidate.assessment_score,
        assessment_status=AssessmentStatus.NOT_TAKEN
        if candidate.assessment_score is None
        else AssessmentStatus.PASSED,
        grade_changed_at=assessed,
        fsp_member_id=candidate.fsp_member_id,
        fsp_achievements=[
            FspAchievement(
                id=seed_id("fsp", f"{candidate.key}:{index}"),
                event_name=item.event_name,
                discipline=item.discipline,
                level=item.level,
                year=item.year,
                place=item.place,
            )
            for index, item in enumerate(candidate.fsp_achievements)
        ],
        phone=candidate.phone,
        telegram=candidate.telegram,
        is_visible_to_employers=candidate.is_visible_to_employers,
        created_at=registered,
        updated_at=assessed or registered,
    )


async def _ensure_no_foreign_accounts(
    session: AsyncSession, emails: list[str], user_ids: list[uuid.UUID]
) -> None:
    taken = await session.scalars(
        select(User.email).where(User.email.in_(emails), User.id.not_in(user_ids))
    )
    conflicts = sorted(taken)
    if conflicts:
        msg = (
            "Demo emails are taken by accounts the seed did not create: "
            f"{', '.join(conflicts)}. Remove those accounts or change the fixtures."
        )
        raise SeedConflictError(msg)


async def _clear(session: AsyncSession, user_ids: list[uuid.UUID]) -> None:
    """Deletes demo rows and everything attached to them, children first.

    Explicit order instead of ON DELETE CASCADE: SQLite (tests) does not enforce foreign keys.
    """
    profiles = select(CandidateProfile.id).where(CandidateProfile.user_id.in_(user_ids))
    companies = select(Company.id).where(Company.owner_id.in_(user_ids))
    vacancies = select(Vacancy.id).where(Vacancy.company_id.in_(companies))
    attempts = select(AssessmentAttempt.id).where(AssessmentAttempt.candidate_id.in_(profiles))
    statements = (
        # Feed decisions by demo accounts and on demo cards, by anyone.
        delete(VacancyReaction).where(
            or_(VacancyReaction.user_id.in_(user_ids), VacancyReaction.vacancy_id.in_(vacancies))
        ),
        delete(CandidateReaction).where(
            or_(
                CandidateReaction.user_id.in_(user_ids),
                CandidateReaction.candidate_id.in_(profiles),
            )
        ),
        delete(AssessmentAnswer).where(AssessmentAnswer.attempt_id.in_(attempts)),
        delete(AssessmentAttempt).where(AssessmentAttempt.candidate_id.in_(profiles)),
        delete(AssessmentTest).where(AssessmentTest.owner_id.in_(user_ids)),
        delete(AssessmentTask).where(AssessmentTask.owner_id.in_(user_ids)),
        delete(Invitation).where(
            or_(Invitation.candidate_id.in_(profiles), Invitation.company_id.in_(companies))
        ),
        delete(FspAchievement).where(FspAchievement.candidate_id.in_(profiles)),
        delete(Vacancy).where(Vacancy.company_id.in_(companies)),
        delete(CandidateProfile).where(CandidateProfile.user_id.in_(user_ids)),
        delete(Company).where(Company.owner_id.in_(user_ids)),
        delete(EmailVerificationCode).where(EmailVerificationCode.user_id.in_(user_ids)),
        delete(User).where(User.id.in_(user_ids)),
    )
    for statement in statements:
        # Nothing of this is loaded in the session, so there is nothing to synchronise.
        await session.execute(statement.execution_options(synchronize_session=False))


async def seed_database(
    session: AsyncSession, data: SeedData, *, password_hash: str, now: datetime | None = None
) -> SeedSummary:
    """Replaces the demo rows. The caller commits; invitations to demo profiles are dropped too."""
    now = now or datetime.now(UTC)
    users = [_employer(company, password_hash, now) for company in data.companies]
    users += [_candidate_user(candidate, password_hash, now) for candidate in data.candidates]
    user_ids = [user.id for user in users]

    await _ensure_no_foreign_accounts(session, [user.email for user in users], user_ids)
    await _clear(session, user_ids)

    # Flushed level by level: the tables have foreign keys but no ORM relationships between them.
    session.add_all(users)
    await session.flush()
    session.add_all(_company(company, now) for company in data.companies)
    await session.flush()
    session.add_all(_vacancy(vacancy, order, now) for order, vacancy in enumerate(data.vacancies))
    session.add_all(_candidate(candidate, now) for candidate in data.candidates)
    await session.flush()

    return SeedSummary(
        companies=len(data.companies),
        vacancies=len(data.vacancies),
        candidates=len(data.candidates),
        fsp_achievements=sum(len(candidate.fsp_achievements) for candidate in data.candidates),
    )
