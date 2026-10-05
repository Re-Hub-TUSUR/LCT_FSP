import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EmailVerificationCode


class EmailVerificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_user(self, user_id: uuid.UUID) -> EmailVerificationCode | None:
        result = await self._session.execute(
            select(EmailVerificationCode).where(EmailVerificationCode.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def add(self, code: EmailVerificationCode) -> EmailVerificationCode:
        self._session.add(code)
        await self._session.flush()
        return code

    async def delete(self, code: EmailVerificationCode) -> None:
        await self._session.delete(code)
        await self._session.flush()

    async def commit(self) -> None:
        """Commit before an error response, which would otherwise roll the session back."""
        await self._session.commit()
