"""ORM rows → public API schemas. Only this layer decides which fields leave the backend."""

from pydantic import ValidationError

from app.models import CandidateProfile, Company, Vacancy, WorkFormat
from app.models.enums import EmploymentType, Grade, VacancyBenefit
from app.schemas.candidate import (
    CandidateContacts,
    CandidateRead,
    EducationEntry,
    ExperienceEntry,
    FspAchievementRead,
    OwnCandidateRead,
    ResumeRead,
)
from app.schemas.category import Category
from app.schemas.common import ApiModel, SalaryRange
from app.schemas.company import CompanyRead
from app.schemas.vacancy import CompanyBrief, VacancyRead
from app.services.age import ADULT_AGE, age_on
from app.services.categories import category_for


def company_read(company: Company) -> CompanyRead:
    return CompanyRead.model_validate(company).model_copy(
        update={"has_logo": company.logo_type is not None}
    )


def company_brief(company: Company) -> CompanyBrief:
    return CompanyBrief(
        id=company.id,
        name=company.name,
        industry=company.industry,
        city=company.city,
        size=company.size,
        it_accredited=company.it_accredited,
        has_logo=company.logo_type is not None,
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
        grades=[Grade(value) for value in vacancy.grades or [vacancy.grade]],
        stack_required=list(vacancy.stack_required or vacancy.stack),
        stack_nice=list(vacancy.stack_nice or []),
        relocation_help=vacancy.relocation_help,
        employment_types=[EmploymentType(value) for value in vacancy.employment_types or []],
        benefits=[VacancyBenefit(value) for value in vacancy.benefits or []],
        verified_grade_only=vacancy.verified_grade_only,
        fsp_best_result=vacancy.fsp_best_result,
        fsp_discipline=vacancy.fsp_discipline,
        min_experience_years=vacancy.min_experience_years,
    )


def profile_category(profile: CandidateProfile) -> Category | None:
    return category_for(profile.specialization, profile.grade)


def resume_views(profile: CandidateProfile) -> list[ResumeRead]:
    """Priority resume first. Extra resumes keep the id they were stored with."""
    primary = ResumeRead(
        id=profile.id,
        headline=profile.headline,
        specialization=profile.specialization,
        stack=list(profile.stack),
        soft_skills=list(profile.soft_skills),
        about=profile.about,
        experience_years=profile.experience_years,
        is_primary=True,
    )
    extras: list[ResumeRead] = []
    for item in profile.additional_resumes or []:
        if not isinstance(item, dict) or "id" not in item:
            continue
        extras.append(
            ResumeRead(
                id=item["id"],
                headline=stored_text(item.get("headline")),
                specialization=stored_text(item.get("specialization")),
                stack=stored_skills(item.get("stack")),
                soft_skills=stored_skills(item.get("soft_skills")),
                about=stored_text(item.get("about")),
                experience_years=stored_years(item.get("experience_years")),
                is_primary=False,
            )
        )
    return [primary, *extras]


def stored_text(value: object) -> str | None:
    return value if isinstance(value, str) else None


def stored_skills(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def stored_years(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


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
        resumes=resume_views(profile),
        has_photo=profile.photo_type is not None,
        job_status=profile.job_status,
        employment_types=[EmploymentType(value) for value in profile.employment_types or []],
        experience_entries=stored_entries(profile.experience_entries, ExperienceEntry),
        no_experience=profile.no_experience,
        education=stored_entries(profile.education, EducationEntry),
        github_url=profile.github_url,
        is_minor=profile.birth_date is not None and age_on(profile.birth_date) < ADULT_AGE,
        last_active_at=profile.last_active_at,
        contacts=contacts,
    )


def stored_entries[T: ApiModel](items: object, model: type[T]) -> list[T]:
    """JSON rows written by this backend; a row that no longer validates is skipped."""
    if not isinstance(items, list):
        return []
    result: list[T] = []
    for item in items:
        try:
            result.append(model.model_validate(item))
        except ValidationError:
            continue
    return result


def own_candidate_read(profile: CandidateProfile, *, email: str) -> OwnCandidateRead:
    """Full profile for the signed-in candidate, including contacts and cabinet switches."""
    public = candidate_read(
        profile,
        contacts=CandidateContacts(email=email, phone=profile.phone, telegram=profile.telegram),
    )
    return OwnCandidateRead.model_validate(
        {
            **public.model_dump(),
            "searching": profile.is_visible_to_employers,
            "fsp_member_id": profile.fsp_member_id,
            "specialization": profile.specialization,
            "birth_date": profile.birth_date,
            "profile_display_consent": profile.profile_display_consent,
            "fsp_sync": profile.fsp_sync,
        }
    )
