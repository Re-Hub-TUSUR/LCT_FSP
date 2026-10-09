"""Platform parameters: defaults in code, changes in `admin_parameters`, every change journaled."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.audit import AuditLog
from app.admin.dictionaries import DEFAULTS, HARDCODED, PARAMETER_SPECS, PARAMETERS
from app.admin.models import AdminParameter
from app.admin.schemas import HardcodedRead, ParameterRead, ParametersRead
from app.core.errors import AppError, NotFoundError
from app.models import User


class ParameterService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditLog(session)

    async def _stored(self) -> dict[str, AdminParameter]:
        rows = await self._session.scalars(select(AdminParameter))
        return {row.key: row for row in rows}

    async def values(self) -> dict[str, int]:
        """Every parameter: the stored value or the default."""
        stored = await self._stored()
        return {
            key: int(stored[key].value) if key in stored else default
            for key, default in DEFAULTS.items()
        }

    async def read(self) -> ParametersRead:
        stored = await self._stored()
        return ParametersRead(
            items=[
                ParameterRead(
                    key=spec.key,
                    label=spec.label,
                    value=int(stored[spec.key].value) if spec.key in stored else spec.default,
                    default=spec.default,
                    minimum=spec.minimum,
                    maximum=spec.maximum,
                    unit=spec.unit,
                    updated_at=stored[spec.key].updated_at if spec.key in stored else None,
                )
                for spec in PARAMETERS
            ],
            hardcoded=[
                HardcodedRead(parameter=item.parameter, where=item.where) for item in HARDCODED
            ],
        )

    async def update(self, actor: User, key: str, value: int) -> ParametersRead:
        spec = PARAMETER_SPECS.get(key)
        if spec is None:
            raise NotFoundError("Параметр не найден")
        if not spec.minimum <= value <= spec.maximum:
            raise AppError(f"Значение должно быть от {spec.minimum} до {spec.maximum}")
        values = await self.values()
        _check_consistent({**values, key: value})
        old = values[key]
        if old != value:
            row = await self._session.get(AdminParameter, key)
            if row is None:
                row = AdminParameter(key=key, value=value)
                self._session.add(row)
            row.value = value
            row.updated_at = datetime.now(UTC)
            row.updated_by = actor.id
            await self._session.flush()
            await self._audit.record(actor, "parameter", key, "update", {"value": [old, value]})
        return await self.read()


def _check_consistent(values: dict[str, int]) -> None:
    if values["target_solve_min"] > values["target_solve_max"]:
        raise AppError("Нижняя граница целевой доли решивших больше верхней")
