"""FSP participant registry: achievements and sport titles by participant id.

The platform reads it with its own service account (OAuth2 client credentials of the same
Keycloak client), so a re-sync never needs the candidate to sign in to FSP ID again.
"""

from typing import Final, Protocol
from urllib.parse import quote

from pydantic import ValidationError

from app.core.config import Settings
from app.integrations.fsp.http import HttpCallError, get_json, post_form
from app.integrations.fsp.schemas import FspMemberRecord

_NOT_FOUND: Final = 404


class FspRegistryError(Exception):
    """The registry did not answer or answered nonsense; `message` is shown to the candidate."""

    def __init__(self, message: str = "Реестр ФСП временно недоступен") -> None:
        super().__init__(message)
        self.message = message


class FspRegistryClient(Protocol):
    async def fetch_member(self, member_id: str) -> FspMemberRecord:
        """A participant unknown to the registry is an empty record, not an error."""
        ...


class HttpFspRegistryClient:
    def __init__(self, settings: Settings) -> None:
        self._base = settings.fsp_registry_url.rstrip("/")
        self._token_url = f"{settings.fsp_id_issuer.rstrip('/')}/protocol/openid-connect/token"
        self._client_id = settings.fsp_id_client_id
        self._client_secret = settings.fsp_id_client_secret.get_secret_value()

    async def fetch_member(self, member_id: str) -> FspMemberRecord:
        if not self._base:
            raise FspRegistryError("Адрес реестра ФСП не настроен")
        try:
            token = await self._service_token()
            body = await get_json(f"{self._base}/members/{quote(member_id, safe='')}", bearer=token)
        except HttpCallError as exc:
            if exc.status == _NOT_FOUND:
                return FspMemberRecord(member_id=member_id)
            raise FspRegistryError() from exc
        try:
            record = FspMemberRecord.model_validate(body)
        except ValidationError as exc:
            raise FspRegistryError("Реестр ФСП вернул данные в неизвестном формате") from exc
        if record.member_id != member_id:
            raise FspRegistryError("Реестр ФСП вернул данные другого участника")
        return record

    async def _service_token(self) -> str:
        body = await post_form(
            self._token_url,
            {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        token = body.get("access_token")
        if not isinstance(token, str):
            msg = "no access_token in the token response"
            raise HttpCallError(msg)
        return token
