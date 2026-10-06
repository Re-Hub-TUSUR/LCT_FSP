"""Read access to a single candidate profile under the visibility rules of ТЗ 2.1–2.2."""

import uuid

from app.core.errors import NotFoundError
from app.models import User, UserRole
from app.repositories.candidate import CandidateRepository
from app.repositories.invitation import InvitationRepository
from app.schemas.candidate import CandidateContacts, CandidateRead
from app.services.presenters import candidate_read


class CandidateProfileService:
    def __init__(self, candidates: CandidateRepository, invitations: InvitationRepository) -> None:
        self._candidates = candidates
        self._invitations = invitations

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
        return candidate_read(profile, contacts=contacts)
