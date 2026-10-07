"""Employer side of the company document check: upload PDFs, see the decision."""

import uuid
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from app.admin.dependencies import VerificationDep
from app.admin.schemas import VerificationRead
from app.admin.services.verification import DOCUMENT_LIMIT
from app.dependencies.auth import EmployerUser

router = APIRouter(prefix="/companies/me/verification", tags=["companies"])


@router.get("", summary="The state of the company's check and its documents")
async def read_verification(user: EmployerUser, service: VerificationDep) -> VerificationRead:
    return await service.mine(user)


@router.post(
    "/documents",
    status_code=status.HTTP_201_CREATED,
    summary="Upload an official document (PDF, up to 10 MB): the request goes to admins",
)
async def upload_document(
    user: EmployerUser, service: VerificationDep, file: Annotated[UploadFile, File()]
) -> VerificationRead:
    # One byte over the limit is enough to know the file is too big.
    data = await file.read(DOCUMENT_LIMIT + 1)
    return await service.upload(user, file.filename, data)


@router.delete(
    "/documents/{document_id}", summary="Remove a document until the company is approved"
)
async def delete_document(
    document_id: uuid.UUID, user: EmployerUser, service: VerificationDep
) -> VerificationRead:
    return await service.remove(user, document_id)
