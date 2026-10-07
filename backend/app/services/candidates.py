"""Read and edit a candidate profile under the visibility rules of ТЗ 2.1–2.2."""

import uuid

from app.core.errors import AppError, ConflictError, NotFoundError
from app.models import AssessmentStatus, CandidateProfile, User, UserRole
from app.repositories.candidate import CandidateRepository
from app.repositories.company import CompanyRepository
from app.repositories.invitation import InvitationRepository
from app.repositories.reaction import ReactionRepository
from app.schemas.candidate import (
    CandidateContacts,
    CandidateProfileUpdate,
    CandidateRead,
    OwnCandidateRead,
    ResumeCreate,
)
from app.services.categories import SPECIALIZATIONS
from app.services.presenters import (
    candidate_read,
    own_candidate_read,
    stored_skills,
    stored_text,
    stored_years,
)
from app.services.uploads import PHOTO_LIMIT, sniff_image

MAX_RESUMES = 3
MAX_SKILL_LENGTH = 40


class CandidateProfileService:
    def __init__(
        self,
        candidates: CandidateRepository,
        invitations: InvitationRepository,
        reactions: ReactionRepository,
        companies: CompanyRepository,
    ) -> None:
        self._candidates = candidates
        self._invitations = invitations
        self._reactions = reactions
        self._companies = companies

    async def read(self, candidate_id: uuid.UUID, viewer: User) -> CandidateRead:
        """Candidates see only themselves; employers see visible profiles.

        Contacts are shown to the candidate and to an employer whose invitation the candidate
        accepted. Hidden and foreign profiles answer 404 so their existence is not revealed.
        """
        profile = await self._candidates.get(candidate_id)
        if profile is None:
            raise NotFoundError("Кандидат не найден")
        own = profile.user_id == viewer.id
        employer = viewer.role == UserRole.EMPLOYER
        if not (
            own or viewer.role == UserRole.ADMIN or (employer and profile.is_visible_to_employers)
        ):
            raise NotFoundError("Кандидат не найден")

        contacts = None
        if own or (
            employer and await self._invitations.accepted_from_owner(candidate_id, viewer.id)
        ):
            email = await self._candidates.email_of(profile)
            contacts = CandidateContacts(
                email=email or "", phone=profile.phone, telegram=profile.telegram
            )
        matched = None
        if employer:
            company = await self._companies.get_by_owner(viewer.id)
            matched = company is not None and await self._reactions.is_match(
                recruiter_id=viewer.id,
                company_id=company.id,
                candidate_id=profile.id,
                candidate_user_id=profile.user_id,
            )
        return candidate_read(profile, contacts=contacts).model_copy(update={"matched": matched})

    async def read_own(self, user: User) -> OwnCandidateRead:
        return own_candidate_read(await self._require(user), email=user.email)

    async def save_resume(self, user: User, data: CandidateProfileUpdate) -> OwnCandidateRead:
        profile = await self._candidates.get_by_user(user.id)
        if profile is None:
            _require_resume(data)
            profile = CandidateProfile(
                user_id=user.id,
                display_name=data.display_name.strip() if data.display_name else "",
                assessment_status=AssessmentStatus.NOT_TAKEN,
                is_visible_to_employers=True,
                stack=[],
                soft_skills=[],
                work_formats=[],
                additional_resumes=[],
            )
            profile.fsp_achievements = []
            _apply_resume(profile, data)
            await self._candidates.add(profile)
        else:
            _apply_resume(profile, data)
        return own_candidate_read(profile, email=user.email)

    async def set_searching(self, user: User, searching: bool) -> OwnCandidateRead:
        profile = await self._require(user)
        profile.is_visible_to_employers = searching
        return own_candidate_read(profile, email=user.email)

    async def link_fsp(self, user: User, member_id: str) -> OwnCandidateRead:
        profile = await self._require(user)
        member_id = member_id.strip()
        other = await self._candidates.get_by_fsp_member(member_id)
        if other is not None and other.id != profile.id:
            raise ConflictError("Этот ID участника ФСП уже связан с другим аккаунтом")
        if profile.fsp_member_id != member_id:
            profile.fsp_achievements.clear()
            profile.fsp_member_id = member_id
        return own_candidate_read(profile, email=user.email)

    async def unlink_fsp(self, user: User) -> OwnCandidateRead:
        profile = await self._require(user)
        profile.fsp_achievements.clear()
        profile.fsp_member_id = None
        return own_candidate_read(profile, email=user.email)

    async def add_resume(self, user: User, data: ResumeCreate) -> OwnCandidateRead:
        profile = await self._require(user)
        extras = list(profile.additional_resumes or [])
        if 1 + len(extras) >= MAX_RESUMES:
            raise AppError("Можно сохранить не больше трёх резюме")
        if data.specialization not in SPECIALIZATIONS:
            raise AppError("Выберите специализацию из списка")
        stack = _skills(data.stack, limit=30, label="Стек")
        if not stack:
            raise AppError("Укажите хотя бы один навык")
        extras.append(
            {
                "id": str(uuid.uuid4()),
                "headline": data.headline.strip(),
                "specialization": data.specialization,
                "stack": stack,
                "soft_skills": _skills(data.soft_skills, limit=20, label="Софт-скиллы"),
                "about": data.about.strip() if data.about else None,
                "experience_years": data.experience_years,
            }
        )
        profile.additional_resumes = extras
        return own_candidate_read(profile, email=user.email)

    async def make_primary(self, user: User, resume_id: uuid.UUID) -> OwnCandidateRead:
        """Swap the chosen resume into the columns search and the feed rank first."""
        profile = await self._require(user)
        if resume_id == profile.id:
            return own_candidate_read(profile, email=user.email)
        extras = list(profile.additional_resumes or [])
        chosen = next((item for item in extras if str(item.get("id")) == str(resume_id)), None)
        if chosen is None:
            raise NotFoundError("Резюме не найдено")
        previous: dict[str, object] = {
            "id": str(uuid.uuid4()),
            "headline": profile.headline,
            "specialization": profile.specialization,
            "stack": list(profile.stack),
            "soft_skills": list(profile.soft_skills),
            "about": profile.about,
            "experience_years": profile.experience_years,
        }
        profile.headline = stored_text(chosen.get("headline"))
        profile.specialization = stored_text(chosen.get("specialization"))
        profile.stack = stored_skills(chosen.get("stack"))
        profile.soft_skills = stored_skills(chosen.get("soft_skills"))
        profile.about = stored_text(chosen.get("about"))
        profile.experience_years = stored_years(chosen.get("experience_years"))
        profile.additional_resumes = [
            previous if str(item.get("id")) == str(resume_id) else item for item in extras
        ]
        return own_candidate_read(profile, email=user.email)

    async def set_photo(self, user: User, data: bytes) -> OwnCandidateRead:
        profile = await self._require(user)
        if len(data) > PHOTO_LIMIT:
            raise AppError("Фото больше 2 МБ")
        media = sniff_image(data)
        if media is None:
            raise AppError("Нужна фотография JPEG, PNG или WebP")
        profile.photo = data
        profile.photo_type = media
        return own_candidate_read(profile, email=user.email)

    async def clear_photo(self, user: User) -> OwnCandidateRead:
        profile = await self._require(user)
        profile.photo = None
        profile.photo_type = None
        return own_candidate_read(profile, email=user.email)

    async def open_photo(self, candidate_id: uuid.UUID, viewer: User) -> tuple[bytes, str]:
        profile = await self._candidates.get(candidate_id)
        if profile is None:
            raise NotFoundError("Кандидат не найден")
        own = profile.user_id == viewer.id
        employer = viewer.role == UserRole.EMPLOYER
        if not (
            own or viewer.role == UserRole.ADMIN or (employer and profile.is_visible_to_employers)
        ):
            raise NotFoundError("Кандидат не найден")
        photo = await self._candidates.photo_of(profile.id)
        if photo is None:
            raise NotFoundError("Фото не загружено")
        return photo

    async def _require(self, user: User) -> CandidateProfile:
        profile = await self._candidates.get_by_user(user.id)
        if profile is None:
            raise NotFoundError("Сначала сохраните резюме")
        return profile


def _require_resume(data: CandidateProfileUpdate) -> None:
    missing: list[str] = []
    if not data.display_name:
        missing.append("имя")
    if not data.headline:
        missing.append("должность")
    if not data.specialization:
        missing.append("специализацию")
    if not data.city:
        missing.append("город")
    if "experience_years" not in data.model_fields_set or data.experience_years is None:
        missing.append("стаж")
    if not data.stack:
        missing.append("стек")
    if not data.work_formats:
        missing.append("формат работы")
    if missing:
        raise AppError("Заполните: " + ", ".join(missing))


def _apply_resume(profile: CandidateProfile, data: CandidateProfileUpdate) -> None:
    _apply_texts(profile, data)
    _apply_terms(profile, data)


def _apply_texts(profile: CandidateProfile, data: CandidateProfileUpdate) -> None:
    """Free-text fields: they are only trimmed, never rejected."""
    fields = data.model_fields_set
    if "display_name" in fields and data.display_name is not None:
        profile.display_name = data.display_name.strip()
    if "headline" in fields:
        profile.headline = data.headline.strip() if data.headline else None
    if "about" in fields:
        profile.about = data.about.strip() if data.about else None
    if "city" in fields:
        profile.city = data.city.strip() if data.city else None
    if "phone" in fields:
        profile.phone = _blank(data.phone)
    if "telegram" in fields:
        profile.telegram = _telegram(data.telegram)


def _apply_terms(profile: CandidateProfile, data: CandidateProfileUpdate) -> None:
    """Skills and work terms: the fields that can be rejected."""
    fields = data.model_fields_set
    if "stack" in fields:
        profile.stack = _skills(data.stack or [], limit=30, label="Стек")
        if not profile.stack:
            raise AppError("Укажите хотя бы один навык")
    if "soft_skills" in fields:
        profile.soft_skills = _skills(data.soft_skills or [], limit=20, label="Софт-скиллы")
    if "experience_years" in fields:
        profile.experience_years = data.experience_years
    if "work_formats" in fields:
        if not data.work_formats:
            raise AppError("Выберите формат работы")
        profile.work_formats = list(dict.fromkeys(item.value for item in data.work_formats))
    if "salary_expectation" in fields:
        profile.salary_expectation = data.salary_expectation
    if "specialization" in fields:
        if data.specialization not in SPECIALIZATIONS:
            raise AppError("Выберите специализацию из списка")
        profile.specialization = data.specialization


def _skills(values: list[str], *, limit: int, label: str) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in values:
        skill = " ".join(raw.split())
        if not skill:
            continue
        if len(skill) > MAX_SKILL_LENGTH:
            raise AppError(
                f"{label}: «{skill[:MAX_SKILL_LENGTH]}» длиннее {MAX_SKILL_LENGTH} символов"
            )
        key = skill.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(skill)
    if len(cleaned) > limit:
        raise AppError(f"{label}: не больше {limit}")
    return cleaned


def _blank(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _telegram(value: str | None) -> str | None:
    text = _blank(value)
    if text is None:
        return None
    text = text.lstrip("@").strip()
    return text or None
