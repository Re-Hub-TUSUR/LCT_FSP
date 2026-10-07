import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, Query, Response, UploadFile, status

from app.dependencies.auth import CurrentUser, EmployerUser
from app.dependencies.services import ChatServiceDep
from app.schemas.chat import (
    ChatMeetingCreate,
    ConversationRead,
    MessagePage,
    MessageRead,
    TextMessageCreate,
)
from app.services.uploads import CHAT_ATTACHMENT_LIMIT

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", summary="Matched chats")
async def list_conversations(user: CurrentUser, service: ChatServiceDep) -> list[ConversationRead]:
    return await service.list_conversations(user)


@router.get("/{conversation_id}", summary="One chat")
async def get_conversation(
    user: CurrentUser, conversation_id: uuid.UUID, service: ChatServiceDep
) -> ConversationRead:
    return await service.get_conversation(user, conversation_id)


@router.get("/{conversation_id}/messages", summary="Message history")
async def list_messages(
    user: CurrentUser,
    conversation_id: uuid.UUID,
    service: ChatServiceDep,
    before: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> MessagePage:
    return await service.list_messages(user, conversation_id, before=before, limit=limit)


@router.post(
    "/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Send a text message",
)
async def send_text(
    user: CurrentUser,
    conversation_id: uuid.UUID,
    data: TextMessageCreate,
    service: ChatServiceDep,
) -> MessageRead:
    return await service.send_text(user, conversation_id, data.text)


@router.post(
    "/{conversation_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    summary="Send a photo or document",
)
async def send_attachment(
    user: CurrentUser,
    conversation_id: uuid.UUID,
    service: ChatServiceDep,
    file: Annotated[UploadFile, File()],
) -> MessageRead:
    data = await file.read(CHAT_ATTACHMENT_LIMIT + 1)
    return await service.send_attachment(
        user,
        conversation_id,
        filename=file.filename or "file",
        data=data,
    )


@router.get("/attachments/{attachment_id}", summary="Download a chat attachment")
async def download_attachment(
    user: CurrentUser,
    attachment_id: uuid.UUID,
    service: ChatServiceDep,
) -> Response:
    attachment, data = await service.load_attachment_bytes(user, attachment_id)
    return Response(
        content=data,
        media_type=attachment.media_type,
        headers={"Content-Disposition": f'inline; filename="{attachment.filename}"'},
    )


@router.post(
    "/{conversation_id}/meetings",
    status_code=status.HTTP_201_CREATED,
    summary="Employer: schedule a meeting into the chat and calendar",
)
async def send_meeting(
    user: EmployerUser,
    conversation_id: uuid.UUID,
    data: ChatMeetingCreate,
    service: ChatServiceDep,
) -> MessageRead:
    return await service.send_meeting(user, conversation_id, data)
