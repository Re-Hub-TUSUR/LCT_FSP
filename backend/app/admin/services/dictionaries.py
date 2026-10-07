"""Specializations, grades and skills of the admin panel.

The first read fills empty tables from what the platform already uses: the specializations of
`app.services.categories` and the topics of the platform bank. The platform itself keeps reading
its code dictionary, so a specialization added here is marked `inPlatform: false`.
"""

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.audit import AuditLog
from app.admin.dictionaries import GRADES
from app.admin.models import AdminSkill, AdminSpecialization
from app.admin.schemas import (
    DictionariesRead,
    GradeRead,
    SkillCreate,
    SkillRead,
    SkillUpdate,
    SpecializationCreate,
    SpecializationRead,
    SpecializationUpdate,
)
from app.core.errors import ConflictError, NotFoundError
from app.models import AssessmentTask, User
from app.services.categories import SPECIALIZATIONS


class DictionaryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditLog(session)

    async def _ensure_defaults(self) -> None:
        if await self._session.scalar(select(func.count()).select_from(AdminSpecialization)):
            return
        try:
            # A savepoint: two first requests may race here, the loser keeps the winner's rows.
            async with self._session.begin_nested():
                await self._fill_defaults()
        except IntegrityError:
            return

    async def _fill_defaults(self) -> None:
        for order, (code, label) in enumerate(SPECIALIZATIONS.items()):
            self._session.add(AdminSpecialization(code=code, label=label, sort_order=order))
        await self._session.flush()
        if await self._session.scalar(select(func.count()).select_from(AdminSkill)):
            return
        rows = await self._session.execute(
            select(AssessmentTask.topic, AssessmentTask.specializations).where(
                AssessmentTask.owner_id.is_(None)
            )
        )
        pairs = {
            (code, topic)
            for topic, codes in rows
            for code in codes
            if code in SPECIALIZATIONS and topic
        }
        for code, topic in sorted(pairs):
            self._session.add(AdminSkill(specialization_code=code, name=topic[:64]))
        await self._session.flush()

    async def read(self) -> DictionariesRead:
        await self._ensure_defaults()
        specializations = await self._session.scalars(
            select(AdminSpecialization).order_by(
                AdminSpecialization.sort_order, AdminSpecialization.code
            )
        )
        skills = await self._session.scalars(
            select(AdminSkill).order_by(AdminSkill.specialization_code, AdminSkill.name)
        )
        return DictionariesRead(
            specializations=[_specialization(item) for item in specializations],
            grades=[GradeRead(code=g.code, label=g.label, base=g.base.value) for g in GRADES],
            skills=[SkillRead.model_validate(item) for item in skills],
        )

    async def add_specialization(self, actor: User, data: SpecializationCreate) -> DictionariesRead:
        await self._ensure_defaults()
        if await self._session.get(AdminSpecialization, data.code) is not None:
            raise ConflictError("Специализация с таким кодом уже есть")
        order = await self._session.scalar(select(func.max(AdminSpecialization.sort_order)))
        self._session.add(
            AdminSpecialization(code=data.code, label=data.label, sort_order=(order or 0) + 1)
        )
        await self._session.flush()
        await self._audit.record(
            actor, "specialization", data.code, "create", {"label": [None, data.label]}
        )
        return await self.read()

    async def update_specialization(
        self, actor: User, code: str, data: SpecializationUpdate
    ) -> DictionariesRead:
        await self._ensure_defaults()
        item = await self._session.get(AdminSpecialization, code)
        if item is None:
            raise NotFoundError("Специализация не найдена")
        changes: dict[str, list[Any]] = {}
        if data.label is not None and data.label != item.label:
            changes["label"] = [item.label, data.label]
            item.label = data.label
        if data.is_archived is not None and data.is_archived != item.is_archived:
            changes["isArchived"] = [item.is_archived, data.is_archived]
            item.is_archived = data.is_archived
        if changes:
            await self._session.flush()
            await self._audit.record(actor, "specialization", code, "update", changes)
        return await self.read()

    async def add_skill(self, actor: User, data: SkillCreate) -> DictionariesRead:
        await self._ensure_defaults()
        if await self._session.get(AdminSpecialization, data.specialization_code) is None:
            raise NotFoundError("Специализация не найдена")
        name = data.name.strip()
        taken = await self._session.scalar(
            select(AdminSkill.id).where(
                AdminSkill.specialization_code == data.specialization_code,
                AdminSkill.name == name,
            )
        )
        if taken is not None:
            raise ConflictError("Такой навык уже есть в этой специализации")
        skill = AdminSkill(specialization_code=data.specialization_code, name=name)
        self._session.add(skill)
        await self._session.flush()
        await self._audit.record(
            actor,
            "skill",
            skill.id,
            "create",
            {"name": [None, name], "specialization": [None, data.specialization_code]},
        )
        return await self.read()

    async def update_skill(
        self, actor: User, skill_id: uuid.UUID, data: SkillUpdate
    ) -> DictionariesRead:
        skill = await self._session.get(AdminSkill, skill_id)
        if skill is None:
            raise NotFoundError("Навык не найден")
        changes: dict[str, list[Any]] = {}
        if data.name is not None and data.name.strip() != skill.name:
            changes["name"] = [skill.name, data.name.strip()]
            skill.name = data.name.strip()
        if data.is_archived is not None and data.is_archived != skill.is_archived:
            changes["isArchived"] = [skill.is_archived, data.is_archived]
            skill.is_archived = data.is_archived
        if changes:
            await self._session.flush()
            await self._audit.record(actor, "skill", skill.id, "update", changes)
        return await self.read()


def _specialization(item: AdminSpecialization) -> SpecializationRead:
    return SpecializationRead(
        code=item.code,
        label=item.label,
        is_archived=item.is_archived,
        in_platform=item.code in SPECIALIZATIONS,
    )
