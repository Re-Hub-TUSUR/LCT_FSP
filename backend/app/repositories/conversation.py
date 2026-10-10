import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, Message, MessageAttachment


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, conversation_id: uuid.UUID) -> Conversation | None:
        return await self._session.get(Conversation, conversation_id)

    async def get_pair(
        self, *, company_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> Conversation | None:
        return await self._session.scalar(
            select(Conversation).where(
                Conversation.company_id == company_id,
                Conversation.candidate_id == candidate_id,
            )
        )

    async def get_or_create(
        self, *, company_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> Conversation:
        """Both sides open the chat list right after the match: the pair is unique, so the one
        that comes second takes the row of the first instead of failing on the constraint."""
        existing = await self.get_pair(company_id=company_id, candidate_id=candidate_id)
        if existing is not None:
            return existing
        conversation = Conversation(company_id=company_id, candidate_id=candidate_id)
        try:
            async with self._session.begin_nested():
                self._session.add(conversation)
                await self._session.flush()
        except IntegrityError:
            created = await self.get_pair(company_id=company_id, candidate_id=candidate_id)
            if created is None:
                raise
            return created
        await self._session.refresh(conversation)
        return conversation

    async def list_for_company(self, company_id: uuid.UUID) -> list[Conversation]:
        result = await self._session.scalars(
            select(Conversation)
            .where(Conversation.company_id == company_id)
            .order_by(
                Conversation.last_message_at.desc().nullslast(), Conversation.updated_at.desc()
            )
        )
        return list(result)

    async def list_for_candidate(self, candidate_id: uuid.UUID) -> list[Conversation]:
        result = await self._session.scalars(
            select(Conversation)
            .where(Conversation.candidate_id == candidate_id)
            .order_by(
                Conversation.last_message_at.desc().nullslast(), Conversation.updated_at.desc()
            )
        )
        return list(result)

    async def touch(self, conversation_id: uuid.UUID, at: datetime) -> None:
        await self._session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(last_message_at=at)
        )

    async def add_message(self, message: Message) -> Message:
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def list_messages(
        self, conversation_id: uuid.UUID, *, before: datetime | None, limit: int
    ) -> list[Message]:
        stmt = select(Message).where(Message.conversation_id == conversation_id)
        if before is not None:
            stmt = stmt.where(Message.created_at < before)
        stmt = stmt.order_by(Message.created_at.desc()).limit(limit)
        result = await self._session.scalars(stmt)
        return list(reversed(list(result)))

    async def get_attachment(self, attachment_id: uuid.UUID) -> MessageAttachment | None:
        return await self._session.get(MessageAttachment, attachment_id)

    async def add_attachment(self, attachment: MessageAttachment) -> MessageAttachment:
        self._session.add(attachment)
        await self._session.flush()
        await self._session.refresh(attachment)
        return attachment
