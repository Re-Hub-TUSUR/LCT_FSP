"""Linking a candidate profile to FSP ID and importing the FSP registry history.

The main sign-in stays e-mail + password; FSP ID only proves which registry participant the
candidate is. Confirmed results raise the candidate inside a category and never set the grade.

The flow is stateless: `state` is a short-lived JWT bound to the signed-in user, and the PKCE
verifier is an HMAC of its nonce, so the verifier itself never leaves the server.
"""

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Final

import jwt

from app.core.config import Settings
from app.core.errors import AppError, ConflictError, NotFoundError
from app.integrations.fsp.provider import (
    FspIdError,
    FspIdProvider,
    code_challenge,
    redirect_allowed,
)
from app.integrations.fsp.sync import FspSyncService, clear_fsp
from app.models import CandidateProfile, User
from app.repositories.candidate import CandidateRepository
from app.schemas.candidate import FspAuthorizeRead, OwnCandidateRead
from app.services.presenters import own_candidate_read

STATE_TTL: Final = timedelta(minutes=10)
_STATE_TYPE: Final = "fsp_link_state"


class FspLinkService:
    def __init__(
        self,
        candidates: CandidateRepository,
        provider: FspIdProvider,
        sync: FspSyncService,
        settings: Settings,
    ) -> None:
        self._candidates = candidates
        self._provider = provider
        self._sync = sync
        self._settings = settings

    async def authorize(self, user: User, redirect_uri: str) -> FspAuthorizeRead:
        await self._require(user)
        if not redirect_allowed(self._settings, redirect_uri):
            raise AppError("Адрес возврата не зарегистрирован для ФСП ID")
        nonce = secrets.token_urlsafe(16)
        state = self._state(user, nonce=nonce, redirect_uri=redirect_uri)
        url = self._provider.authorize_url(
            state=state,
            nonce=nonce,
            code_challenge=code_challenge(self._verifier(user, nonce)),
            redirect_uri=redirect_uri,
        )
        return FspAuthorizeRead(authorize_url=url)

    async def link(self, user: User, *, code: str, state: str) -> OwnCandidateRead:
        """Exchanges the code, binds the participant id and imports the history.

        A registry failure does not undo the link: `fspSyncError` tells the candidate to retry.
        """
        claims = self._read_state(user, state)
        profile = await self._require(user)
        identity = await self._provider.exchange_code(
            code=code,
            code_verifier=self._verifier(user, claims["nonce"]),
            redirect_uri=claims["ru"],
            nonce=claims["nonce"],
        )
        other = await self._candidates.get_by_fsp_member(identity.member_id)
        if other is not None and other.id != profile.id:
            raise ConflictError("Этот участник ФСП уже связан с другим аккаунтом")
        if profile.fsp_member_id != identity.member_id:
            clear_fsp(profile)
            profile.fsp_member_id = identity.member_id
            profile.fsp_linked_at = datetime.now(UTC)
        await self._sync.sync(profile)
        return own_candidate_read(profile, email=user.email)

    async def resync(self, user: User) -> OwnCandidateRead:
        profile = await self._require(user)
        if profile.fsp_member_id is None:
            raise AppError("Профиль не связан с ФСП ID")
        await self._sync.sync(profile)
        return own_candidate_read(profile, email=user.email)

    async def unlink(self, user: User) -> OwnCandidateRead:
        profile = await self._require(user)
        clear_fsp(profile)
        return own_candidate_read(profile, email=user.email)

    async def _require(self, user: User) -> CandidateProfile:
        profile = await self._candidates.get_by_user(user.id)
        if profile is None:
            raise NotFoundError("Сначала сохраните резюме")
        return profile

    def _secret(self) -> str:
        return self._settings.jwt_secret.get_secret_value()

    def _verifier(self, user: User, nonce: str) -> str:
        digest = hmac.new(
            self._secret().encode("utf-8"), f"fsp-pkce:{user.id}:{nonce}".encode(), hashlib.sha256
        ).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    def _state(self, user: User, *, nonce: str, redirect_uri: str) -> str:
        now = datetime.now(UTC)
        payload = {
            "iss": self._settings.jwt_issuer,
            "typ": _STATE_TYPE,
            "sub": str(user.id),
            "nonce": nonce,
            "ru": redirect_uri,
            "iat": now,
            "exp": now + STATE_TTL,
        }
        return jwt.encode(payload, self._secret(), algorithm=self._settings.jwt_algorithm)

    def _read_state(self, user: User, state: str) -> dict[str, Any]:
        try:
            claims: dict[str, Any] = jwt.decode(
                state,
                self._secret(),
                algorithms=[self._settings.jwt_algorithm],
                issuer=self._settings.jwt_issuer,
                options={"require": ["exp", "sub", "iss"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise FspIdError("Вход через ФСП ID занял слишком долго. Начните заново.") from exc
        except jwt.InvalidTokenError as exc:
            raise FspIdError() from exc
        valid = (
            claims.get("typ") == _STATE_TYPE
            and claims.get("sub") == str(user.id)
            and isinstance(claims.get("nonce"), str)
            and isinstance(claims.get("ru"), str)
        )
        if not valid:
            raise FspIdError("Вход через ФСП ID начат из другого аккаунта")
        return claims
