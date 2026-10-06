import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, token_id: uuid.UUID) -> RefreshToken | None:
        return await self._session.get(RefreshToken, token_id)

    async def add(self, token: RefreshToken) -> None:
        self._session.add(token)
        await self._session.flush()
