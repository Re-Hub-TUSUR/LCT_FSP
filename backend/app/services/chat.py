"""Matched-pair conversations, attachments, and meeting cards."""

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.admin.activity import KIND_CHAT, ActivityRecorder
from app.core.config import Settings
from app.core.errors import AppError, NotFoundError, PermissionDeniedError
from app.models import (
    Conversation,
    Meeting,
    MeetingStatus,
    Message,
    MessageAttachment,
    MessageKind,
    User,
    UserRole,
)
from app.repositories.candidate import CandidateRepository
from app.repositories.company import CompanyRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.meeting import MeetingRepository
from app.repositories.reaction import ReactionRepository
from app.repositories.vacancy import VacancyRepository
from app.schemas.chat import (
    AttachmentRead,
    ChatMeetingCreate,
    ConversationPeer,
    ConversationRead,
    MeetingPreview,
    MessagePage,
    MessageRead,
)
from app.services.notifications import NotificationHub, announce_meeting
from app.services.uploads import CHAT_ATTACHMENT_LIMIT, sniff_chat_attachment


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class ChatService:
    def __init__(
        self,
        *,
        conversations: ConversationRepository,
        reactions: ReactionRepository,
        companies: CompanyRepository,
        candidates: CandidateRepository,
        vacancies: VacancyRepository,
        meetings: MeetingRepository,
        settings: Settings,
        notifications: NotificationHub | None = None,
        activity: ActivityRecorder | None = None,
    ) -> None:
        self._conversations = conversations
        self._reactions = reactions
        self._companies = companies
        self._candidates = candidates
        self._vacancies = vacancies
        self._meetings = meetings
        self._settings = settings
        self._notifications = notifications
        self._activity = activity
        self._upload_root = Path(settings.upload_dir)

    async def list_conversations(self, user: User) -> list[ConversationRead]:
        rows: list[Conversation] = []
        if user.role == UserRole.CANDIDATE:
            profile = await self._candidates.get_by_user(user.id)
            if profile is None:
                return []
            company_ids = await self._reactions.matched_company_ids_for_candidate(
                candidate_user_id=user.id, candidate_id=profile.id
            )
            for company_id in company_ids:
                conv = await self._ensure_conversation(company_id, profile.id)
                rows.append(conv)
        elif user.role == UserRole.EMPLOYER:
            company = await self._companies.get_by_owner(user.id)
            if company is None:
                return []
            matched_ids = await self._reactions.matched_candidate_ids(
                recruiter_id=user.id, company_id=company.id
            )
            for candidate_id in matched_ids:
                conv = await self._ensure_conversation(company.id, candidate_id)
                rows.append(conv)
        else:
            raise AppError("Чаты доступны соискателям и работодателям")

        rows.sort(key=lambda item: (-(item.last_message_at or item.updated_at).timestamp(),))
        result: list[ConversationRead] = []
        for conv in rows:
            peer = await self._peer_for(user, conv)
            result.append(
                ConversationRead(
                    id=conv.id,
                    peer=peer,
                    last_message_at=conv.last_message_at,
                )
            )
        return result

    async def get_conversation(self, user: User, conversation_id: uuid.UUID) -> ConversationRead:
        conv = await self._require_access(user, conversation_id)
        return ConversationRead(
            id=conv.id,
            peer=await self._peer_for(user, conv),
            last_message_at=conv.last_message_at,
        )

    async def list_messages(
        self,
        user: User,
        conversation_id: uuid.UUID,
        *,
        before: datetime | None,
        limit: int = 50,
    ) -> MessagePage:
        conv = await self._require_access(user, conversation_id)
        limit = min(max(limit, 1), 100)
        rows = await self._conversations.list_messages(conv.id, before=before, limit=limit + 1)
        has_more = len(rows) > limit
        page = rows[-limit:] if has_more else rows
        items = [await self._present_message(row) for row in page]
        return MessagePage(items=items, has_more=has_more)

    async def send_text(self, user: User, conversation_id: uuid.UUID, text: str) -> MessageRead:
        conv = await self._require_access(user, conversation_id)
        message = await self._conversations.add_message(
            Message(
                conversation_id=conv.id,
                sender_id=user.id,
                kind=MessageKind.TEXT,
                text=text.strip(),
            )
        )
        await self._conversations.touch(conv.id, _utc(message.created_at))
        read = await self._present_message(message)
        await self._notify_message(conv, read)
        return read

    async def send_attachment(
        self,
        user: User,
        conversation_id: uuid.UUID,
        *,
        filename: str,
        data: bytes,
    ) -> MessageRead:
        conv = await self._require_access(user, conversation_id)
        limit = min(self._settings.chat_attachment_limit, CHAT_ATTACHMENT_LIMIT)
        if len(data) > limit:
            raise AppError("Файл слишком большой")
        media_type = sniff_chat_attachment(data)
        if media_type is None:
            raise AppError("Формат файла не поддерживается")

        storage_key = f"{conv.id}/{uuid.uuid4()}"
        attachment = await self._conversations.add_attachment(
            MessageAttachment(
                conversation_id=conv.id,
                uploader_id=user.id,
                filename=filename[:255] or "file",
                media_type=media_type,
                size_bytes=len(data),
                storage_key=storage_key,
            )
        )
        message = await self._conversations.add_message(
            Message(
                conversation_id=conv.id,
                sender_id=user.id,
                kind=MessageKind.ATTACHMENT,
                attachment_id=attachment.id,
            )
        )
        # Written after the rows: a database error no longer leaves a file nobody knows of.
        path = self._upload_root / storage_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        await self._conversations.touch(conv.id, _utc(message.created_at))
        read = await self._present_message(message)
        if user.role == UserRole.EMPLOYER and self._activity is not None:
            company = await self._companies.get_by_owner(user.id)
            await self._activity.record(KIND_CHAT, user, company, attachment.id)
        await self._notify_message(conv, read)
        return read

    async def send_meeting(
        self, user: User, conversation_id: uuid.UUID, data: ChatMeetingCreate
    ) -> MessageRead:
        if user.role != UserRole.EMPLOYER:
            raise PermissionDeniedError()
        conv = await self._require_access(user, conversation_id)
        company = await self._companies.get(conv.company_id)
        if company is None or company.owner_id != user.id:
            raise NotFoundError("Беседа не найдена")

        starts_at = _utc(data.starts_at)
        ends_at = _utc(data.ends_at) if data.ends_at else starts_at + timedelta(hours=1)
        if ends_at <= starts_at:
            raise AppError("Время окончания должно быть позже начала")
        if starts_at <= datetime.now(UTC):
            raise AppError("Нельзя назначить встречу в прошлом")

        vacancy_id = data.vacancy_id
        if vacancy_id is not None:
            row = await self._vacancies.get(vacancy_id)
            if row is None or row[1].owner_id != user.id:
                raise NotFoundError("Вакансия не найдена")

        meeting = await self._meetings.add(
            Meeting(
                company_id=conv.company_id,
                candidate_id=conv.candidate_id,
                vacancy_id=vacancy_id,
                title=data.title.strip(),
                starts_at=starts_at,
                ends_at=ends_at,
                location=data.location.strip(),
                note=None,
                status=MeetingStatus.PENDING,
            )
        )
        message = await self._conversations.add_message(
            Message(
                conversation_id=conv.id,
                sender_id=user.id,
                kind=MessageKind.MEETING,
                meeting_id=meeting.id,
            )
        )
        await self._conversations.touch(conv.id, _utc(message.created_at))
        read = await self._present_message(message)
        await self._notify_message(conv, read)
        profile = await self._candidates.get(conv.candidate_id)
        if profile is not None:
            await announce_meeting(
                self._notifications,
                user_id=profile.user_id,
                meeting_id=meeting.id,
                company_name=company.name,
                title=meeting.title,
                starts_at=starts_at,
            )
        return read

    async def load_attachment_bytes(
        self, user: User, attachment_id: uuid.UUID
    ) -> tuple[MessageAttachment, bytes]:
        attachment = await self._conversations.get_attachment(attachment_id)
        if attachment is None:
            raise NotFoundError("Файл не найден")
        await self._require_access(user, attachment.conversation_id)
        path = self._upload_root / attachment.storage_key
        if not path.is_file():
            raise NotFoundError("Файл не найден")
        return attachment, path.read_bytes()

    async def _ensure_conversation(
        self, company_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> Conversation:
        return await self._conversations.get_or_create(
            company_id=company_id, candidate_id=candidate_id
        )

    async def _require_access(self, user: User, conversation_id: uuid.UUID) -> Conversation:
        conv = await self._conversations.get(conversation_id)
        if conv is None:
            raise NotFoundError("Беседа не найдена")
        profile = candidate_user_id = None
        if user.role == UserRole.CANDIDATE:
            profile = await self._candidates.get_by_user(user.id)
            if profile is None or profile.id != conv.candidate_id:
                raise NotFoundError("Беседа не найдена")
            candidate_user_id = user.id
        elif user.role == UserRole.EMPLOYER:
            company = await self._companies.get_by_owner(user.id)
            if company is None or company.id != conv.company_id:
                raise NotFoundError("Беседа не найдена")
            profile = await self._candidates.get(conv.candidate_id)
            candidate_user_id = profile.user_id if profile else None
        else:
            raise NotFoundError("Беседа не найдена")

        if profile is None or candidate_user_id is None:
            raise NotFoundError("Беседа не найдена")
        company = await self._companies.get(conv.company_id)
        if company is None:
            raise NotFoundError("Беседа не найдена")
        matched = await self._reactions.is_match(
            recruiter_id=company.owner_id,
            company_id=company.id,
            candidate_id=conv.candidate_id,
            candidate_user_id=candidate_user_id,
        )
        if not matched:
            raise PermissionDeniedError("Чат откроется после взаимной симпатии")
        return conv

    async def _peer_for(self, user: User, conv: Conversation) -> ConversationPeer:
        if user.role == UserRole.CANDIDATE:
            company = await self._companies.get(conv.company_id)
            return ConversationPeer(
                id=conv.company_id,
                name=company.name if company else "",
                subtitle=company.industry if company else None,
            )
        profile = await self._candidates.get(conv.candidate_id)
        return ConversationPeer(
            id=conv.candidate_id,
            name=profile.display_name if profile else "",
            subtitle=profile.headline if profile else None,
        )

    async def _present_message(self, message: Message) -> MessageRead:
        attachment = meeting = None
        if message.attachment_id is not None:
            stored = await self._conversations.get_attachment(message.attachment_id)
            if stored is not None:
                attachment = AttachmentRead(
                    id=stored.id,
                    filename=stored.filename,
                    media_type=stored.media_type,
                    size_bytes=stored.size_bytes,
                )
        if message.meeting_id is not None:
            planned = await self._meetings.get(message.meeting_id)
            if planned is not None:
                meeting = MeetingPreview(
                    id=planned.id,
                    title=planned.title,
                    starts_at=_utc(planned.starts_at),
                    ends_at=_utc(planned.ends_at),
                    location=planned.location,
                    status=planned.status,
                )
        return MessageRead(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            kind=message.kind,
            text=message.text,
            attachment=attachment,
            meeting=meeting,
            created_at=_utc(message.created_at),
        )

    async def _notify_message(self, conv: Conversation, message: MessageRead) -> None:
        if self._notifications is None:
            return
        company = await self._companies.get(conv.company_id)
        profile = await self._candidates.get(conv.candidate_id)
        if company is None or profile is None:
            return
        payload = {
            "type": "message",
            "conversationId": str(conv.id),
            "message": message.model_dump(mode="json"),
        }
        await self._notifications.publish(company.owner_id, payload)
        await self._notifications.publish(profile.user_id, payload)
