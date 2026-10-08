"""Writes the demo dataset into the database, replacing whatever an earlier run wrote."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.enums import VerificationStatus
from app.admin.models import CompanyDocument, CompanyVerification
from app.models import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentStatus,
    AssessmentTask,
    AssessmentTest,
    CandidateCategory,
    CandidateProfile,
    CandidateReaction,
    Company,
    EmailVerificationCode,
    FspAchievement,
    FspSportTitle,
    Invitation,
    Meeting,
    MeetingStatus,
    TestAssignment,
    User,
    UserRole,
    Vacancy,
    VacancyReaction,
)
from app.seed.details import (
    ACCREDITED_COMPANIES,
    candidate_details,
    company_details,
    last_active,
    person,
    vacancy_details,
)
from app.seed.fixtures import CandidateFixture, CompanyFixture, SeedData, VacancyFixture

# Demo accounts share one password. Override it on a public stand with SEED_USER_PASSWORD.
PASSWORD_ENV: Final = "SEED_USER_PASSWORD"  # noqa: S105 - variable name, not a secret
DEFAULT_PASSWORD: Final = "kadry-demo-2026"  # noqa: S105 - documented password of demo accounts

# Matches the default of ASSESSMENT_GRADE_CHANGE_DAYS.
GRADE_CHANGE_DAYS: Final = 90
# Matches the default of ASSESSMENT_RECOMMEND_SCORE.
RECOMMEND_SCORE: Final = 85

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
    fsp_titles: int


def _ago(now: datetime, days: int) -> datetime:
    return now - timedelta(days=days)


def _employer(company: CompanyFixture, password_hash: str, now: datetime) -> User:
    registered = _ago(now, company.registered_days_ago)
    first_name, last_name = person(company.key)
    return User(
        id=seed_id("user", company.key),
        email=company.owner_email,
        password_hash=password_hash,
        role=UserRole.EMPLOYER,
        is_email_verified=True,
        personal_data_consent=True,
        first_name=first_name,
        last_name=last_name,
        last_active_at=last_active(company.key, now),
        created_at=registered,
        updated_at=registered,
    )


def _company(company: CompanyFixture, index: int, now: datetime) -> Company:
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
        **company_details(company, index),
        created_at=registered,
        updated_at=registered,
    )


def _verifications(data: SeedData, now: datetime) -> list[CompanyVerification]:
    """Approved Минцифры extracts of the first companies. No file: the admin sees the decision."""
    return [
        CompanyVerification(
            company_id=seed_id("company", company.key),
            status=VerificationStatus.APPROVED,
            submitted_at=_ago(now, company.registered_days_ago),
            decided_at=_ago(now, max(company.registered_days_ago - 1, 0)),
            decision_reason="Выписка из реестра Минцифры проверена",
        )
        for company in data.companies[:ACCREDITED_COMPANIES]
    ]


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
        **vacancy_details(vacancy),
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
        last_active_at=last_active(candidate.key, now),
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
                external_id=item.id,
                event_name=item.event_name,
                event_kind=item.event_kind,
                discipline=item.discipline,
                level=item.level,
                year=item.year,
                place=item.place,
                result=item.result,
                participation=item.participation,
                team_name=item.team_name,
            )
            for index, item in enumerate(candidate.fsp_achievements)
        ],
        fsp_titles=[
            FspSportTitle(
                id=seed_id("fsp-title", f"{candidate.key}:{index}"),
                external_id=item.id,
                kind=item.kind,
                discipline=item.discipline,
                awarded_year=item.awarded_year,
            )
            for index, item in enumerate(candidate.fsp_titles)
        ],
        # Demo profiles were linked at sign-up and imported from the emulated registry.
        fsp_linked_at=registered if candidate.fsp_member_id else None,
        fsp_synced_at=registered if candidate.fsp_member_id else None,
        phone=candidate.phone,
        telegram=candidate.telegram,
        is_visible_to_employers=candidate.is_visible_to_employers,
        **candidate_details(candidate, now),
        created_at=registered,
        updated_at=assessed or registered,
    )


def _category(candidate: CandidateFixture, now: datetime) -> CandidateCategory | None:
    """The tested grade as a confirmed category; self-declared grades have none."""
    if candidate.assessment_score is None or candidate.assessed_days_ago is None:
        return None
    assessed = _ago(now, candidate.assessed_days_ago)
    return CandidateCategory(
        id=seed_id("category", candidate.key),
        candidate_id=seed_id("candidate", candidate.key),
        specialization=candidate.specialization,
        grade=candidate.grade,
        score=candidate.assessment_score,
        confirmed_at=assessed,
        change_allowed_at=assessed + timedelta(days=GRADE_CHANGE_DAYS),
        recommended_grade=candidate.grade.following
        if candidate.assessment_score >= RECOMMEND_SCORE
        else None,
    )


def _demo_meetings(data: SeedData, now: datetime) -> list[Meeting]:
    """A few interviews of the demo company in the coming days, the demo candidate first."""
    company = data.companies[0]
    invited = [candidate for candidate in data.candidates if candidate.is_visible_to_employers][:3]
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    meetings = []
    for index, candidate in enumerate(invited):
        # 11:00, 13:00 and 15:00 Moscow time on consecutive days.
        starts_at = day + timedelta(days=index + 1, hours=8 + 2 * index)
        meetings.append(
            Meeting(
                id=seed_id("meeting", f"{company.key}:{candidate.key}"),
                company_id=seed_id("company", company.key),
                candidate_id=seed_id("candidate", candidate.key),
                title="Техническое собеседование" if index else "Знакомство с командой",
                starts_at=starts_at,
                ends_at=starts_at + timedelta(hours=1),
                location="https://telemost.yandex.ru/j/00000000000000",
                status=MeetingStatus.CONFIRMED if index == 1 else MeetingStatus.PENDING,
            )
        )
    return meetings


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
        delete(TestAssignment).where(
            or_(
                TestAssignment.candidate_id.in_(profiles),
                TestAssignment.company_id.in_(companies),
            )
        ),
        delete(AssessmentTest).where(AssessmentTest.owner_id.in_(user_ids)),
        delete(AssessmentTask).where(AssessmentTask.owner_id.in_(user_ids)),
        delete(Invitation).where(
            or_(Invitation.candidate_id.in_(profiles), Invitation.company_id.in_(companies))
        ),
        delete(Meeting).where(
            or_(Meeting.candidate_id.in_(profiles), Meeting.company_id.in_(companies))
        ),
        delete(CandidateCategory).where(CandidateCategory.candidate_id.in_(profiles)),
        delete(FspAchievement).where(FspAchievement.candidate_id.in_(profiles)),
        delete(FspSportTitle).where(FspSportTitle.candidate_id.in_(profiles)),
        delete(Vacancy).where(Vacancy.company_id.in_(companies)),
        delete(CompanyDocument).where(CompanyDocument.company_id.in_(companies)),
        delete(CompanyVerification).where(CompanyVerification.company_id.in_(companies)),
        delete(CandidateProfile).where(CandidateProfile.user_id.in_(user_ids)),
        delete(Company).where(Company.owner_id.in_(user_ids)),
        delete(EmailVerificationCode).where(EmailVerificationCode.user_id.in_(user_ids)),
        delete(User).where(User.id.in_(user_ids)),
    )
    for statement in statements:
        # Nothing of this is loaded in the session, so there is nothing to synchronise.
        await session.execute(statement.execution_options(synchronize_session=False))


async def demo_data_loaded(session: AsyncSession, data: SeedData) -> bool:
    """Is any demo account already in the database? Used to seed a fresh stack only once."""
    user_ids = [seed_id("user", company.key) for company in data.companies]
    user_ids += [seed_id("user", candidate.key) for candidate in data.candidates]
    found = await session.scalar(select(User.id).where(User.id.in_(user_ids)).limit(1))
    return found is not None


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
    session.add_all(_company(company, index, now) for index, company in enumerate(data.companies))
    await session.flush()
    session.add_all(_verifications(data, now))
    session.add_all(_vacancy(vacancy, order, now) for order, vacancy in enumerate(data.vacancies))
    session.add_all(_candidate(candidate, now) for candidate in data.candidates)
    await session.flush()
    session.add_all(
        category for candidate in data.candidates if (category := _category(candidate, now))
    )
    session.add_all(_demo_meetings(data, now))
    await session.flush()

    return SeedSummary(
        companies=len(data.companies),
        vacancies=len(data.vacancies),
        candidates=len(data.candidates),
        fsp_achievements=sum(len(candidate.fsp_achievements) for candidate in data.candidates),
        fsp_titles=sum(len(candidate.fsp_titles) for candidate in data.candidates),
    )
