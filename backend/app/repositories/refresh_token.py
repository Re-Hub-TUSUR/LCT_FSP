import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, token_id: uuid.UUID) -> RefreshToken | None:
        return await self._session.get(RefreshToken, token_id)

    async def revoke(self, token_id: uuid.UUID, at: datetime) -> bool:
        """Compare-and-set: true for the one request that revoked a still active token."""
        result = await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.id == token_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=at)
            .execution_options(synchronize_session=False)
        )
        return bool(getattr(result, "rowcount", 0))

    async def add(self, token: RefreshToken) -> None:
        self._session.add(token)
        await self._session.flush()
