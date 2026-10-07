"""Dictionaries, parameters, the action journal and the account list export."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.admin.audit import AuditLog
from app.admin.csv_export import csv_response
from app.admin.dependencies import DictionariesDep, ParametersDep
from app.admin.schemas import (
    AuditEntryRead,
    DictionariesRead,
    ParametersRead,
    ParameterWrite,
    SkillCreate,
    SkillUpdate,
    SpecializationCreate,
    SpecializationUpdate,
)
from app.admin.services.employers import audit_read
from app.dependencies.auth import AdminUser
from app.dependencies.common import SessionDep
from app.dependencies.services import UserRepositoryDep
from app.schemas.common import Page

router = APIRouter()

PER_PAGE = 50
# An edit is journaled as {field: [old, new]}.
_PAIR = 2
Entity = Annotated[str | None, Query(max_length=32)]
EntityId = Annotated[str | None, Query(alias="entityId", max_length=64)]


@router.get("/dictionaries", summary="Specializations, the 11 grades, skills")
async def read_dictionaries(_: AdminUser, service: DictionariesDep) -> DictionariesRead:
    return await service.read()


@router.post("/dictionaries/specializations", summary="Add a specialization")
async def add_specialization(
    user: AdminUser, data: SpecializationCreate, service: DictionariesDep
) -> DictionariesRead:
    return await service.add_specialization(user, data)


@router.patch("/dictionaries/specializations/{code}", summary="Rename or archive a specialization")
async def update_specialization(
    code: str, user: AdminUser, data: SpecializationUpdate, service: DictionariesDep
) -> DictionariesRead:
    return await service.update_specialization(user, code, data)


@router.post("/dictionaries/skills", summary="Add a skill to a specialization")
async def add_skill(
    user: AdminUser, data: SkillCreate, service: DictionariesDep
) -> DictionariesRead:
    return await service.add_skill(user, data)


@router.patch("/dictionaries/skills/{skill_id}", summary="Rename or archive a skill")
async def update_skill(
    skill_id: uuid.UUID, user: AdminUser, data: SkillUpdate, service: DictionariesDep
) -> DictionariesRead:
    return await service.update_skill(user, skill_id, data)


@router.get("/parameters", summary="Platform parameters and where code still hardcodes them")
async def read_parameters(_: AdminUser, service: ParametersDep) -> ParametersRead:
    return await service.read()


@router.put("/parameters/{key}", summary="Change a parameter (journaled)")
async def update_parameter(
    key: str, user: AdminUser, data: ParameterWrite, service: ParametersDep
) -> ParametersRead:
    return await service.update(user, key, data.value)


@router.get("/audit", summary="The journal of admin actions, newest first")
async def read_audit(
    _: AdminUser,
    session: SessionDep,
    entity: Entity = None,
    entity_id: EntityId = None,
    page: Annotated[int, Query(ge=1)] = 1,
) -> Page[AuditEntryRead]:
    entries, total = await AuditLog(session).page(
        entity=entity, entity_id=entity_id, limit=PER_PAGE, offset=(page - 1) * PER_PAGE
    )
    return Page[AuditEntryRead].build(
        [audit_read(entry, email) for entry, email in entries],
        total=total,
        page=page,
        per_page=PER_PAGE,
    )


@router.get("/audit/export.csv", summary="The journal as CSV")
async def export_audit(
    _: AdminUser, session: SessionDep, entity: Entity = None, entity_id: EntityId = None
) -> Response:
    entries, _total = await AuditLog(session).page(
        entity=entity, entity_id=entity_id, limit=10_000, offset=0
    )
    return csv_response(
        "admin-journal.csv",
        ["Дата", "Кто", "Объект", "ID", "Действие", "Изменения", "Причина"],
        (
            [
                entry.created_at.isoformat(),
                email,
                entry.entity,
                entry.entity_id,
                entry.action,
                "; ".join(f"{key}: {old} → {new}" for key, (old, new) in entry.changes.items())
                if all(
                    isinstance(value, list) and len(value) == _PAIR
                    for value in entry.changes.values()
                )
                else str(entry.changes),
                entry.reason,
            ]
            for entry, email in entries
        ),
    )


@router.get("/users/export.csv", summary="Accounts as CSV")
async def export_users(_: AdminUser, users: UserRepositoryDep) -> Response:
    items, _total = await users.list(limit=10_000, offset=0)
    return csv_response(
        "users.csv",
        ["Email", "Роль", "Email подтверждён", "Активен", "Создан"],
        (
            [
                user.email,
                user.role.value,
                user.is_email_verified,
                user.is_active,
                user.created_at.isoformat(),
            ]
            for user in items
        ),
    )
