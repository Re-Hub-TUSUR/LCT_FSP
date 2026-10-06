"""ORM rows → public API schemas. Only this layer decides which fields leave the backend."""

from app.models import CandidateProfile, Company, Vacancy, WorkFormat
from app.schemas.candidate import CandidateContacts, CandidateRead, FspAchievementRead
from app.schemas.category import Category
from app.schemas.common import SalaryRange
from app.schemas.company import CompanyRead
from app.schemas.vacancy import CompanyBrief, VacancyRead
from app.services.categories import category_for


def company_read(company: Company) -> CompanyRead:
    return CompanyRead.model_validate(company)


def company_brief(company: Company) -> CompanyBrief:
    return CompanyBrief(
        id=company.id,
        name=company.name,
        industry=company.industry,
        city=company.city,
        size=company.size,
    )


def vacancy_read(vacancy: Vacancy, company: Company) -> VacancyRead:
    category = category_for(vacancy.specialization, vacancy.grade)
    if category is None:  # pragma: no cover - both columns are NOT NULL
        msg = f"vacancy {vacancy.id} has no category"
        raise ValueError(msg)
    return VacancyRead(
        id=vacancy.id,
        title=vacancy.title,
        company=company_brief(company),
        category=category,
        stack=list(vacancy.stack),
        salary=SalaryRange.model_validate({"from": vacancy.salary_from, "to": vacancy.salary_to}),
        work_format=vacancy.work_format,
        city=vacancy.city,
        description=vacancy.description,
        published_at=vacancy.published_at,
    )


def profile_category(profile: CandidateProfile) -> Category | None:
    return category_for(profile.specialization, profile.grade)


def candidate_read(
    profile: CandidateProfile, *, contacts: CandidateContacts | None = None
) -> CandidateRead:
    """`profile.fsp_achievements` must be loaded. Contacts are passed only when allowed."""
    return CandidateRead(
        id=profile.id,
        display_name=profile.display_name,
        headline=profile.headline,
        about=profile.about,
        category=profile_category(profile),
        grade_verified=profile.assessment_score is not None,
        assessment_score=profile.assessment_score,
        assessment_status=profile.assessment_status,
        stack=list(profile.stack),
        soft_skills=list(profile.soft_skills),
        experience_years=profile.experience_years,
        english_level=profile.english_level,
        city=profile.city,
        relocation_ready=profile.relocation_ready,
        work_formats=[WorkFormat(value) for value in profile.work_formats],
        salary_expectation=profile.salary_expectation,
        fsp_achievements=[
            FspAchievementRead(
                event_name=item.event_name,
                year=item.year,
                place=item.place,
                discipline=item.discipline,
                level=item.level,
            )
            for item in profile.fsp_achievements
        ],
        fsp_linked=profile.fsp_member_id is not None,
        contacts=contacts,
    )
