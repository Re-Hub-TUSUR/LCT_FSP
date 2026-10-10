"""Yandex ID: exchange an authorization code and read the profile.

The secret stays on the server. Tests pass their own client and never call Yandex.
"""

import re
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.core.config import Settings
from app.core.errors import AppError
from app.services.uploads import PHOTO_LIMIT, sniff_image

AUTHORIZE_URL = "https://oauth.yandex.ru/authorize"
CODE_EXCHANGE_URL = "https://oauth.yandex.ru/token"
INFO_URL = "https://login.yandex.ru/info"
# Login and name, portrait, email. Phone and birth date are not requested.
SCOPE = "login:info login:email login:avatar"
_AVATAR_ID = re.compile(r"[A-Za-z0-9/_-]{1,80}")
_DENIED = "Яндекс не подтвердил вход"


@dataclass(frozen=True, slots=True)
class YandexAccount:
    account_id: str
    email: str
    first_name: str
    last_name: str
    portrait: tuple[bytes, str] | None


class YandexDirectory(Protocol):
    async def fetch(self, *, code: str, redirect_uri: str) -> YandexAccount: ...


class HttpYandexDirectory:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._id = settings.yandex_client_id
        self._secret = settings.yandex_client_secret.get_secret_value()
        self._client = client

    async def fetch(self, *, code: str, redirect_uri: str) -> YandexAccount:
        if self._client is not None:
            return await self._read(self._client, code=code, redirect_uri=redirect_uri)
        async with httpx.AsyncClient(timeout=10) as client:
            return await self._read(client, code=code, redirect_uri=redirect_uri)

    async def _read(
        self, client: httpx.AsyncClient, *, code: str, redirect_uri: str
    ) -> YandexAccount:
        try:
            token = await client.post(
                CODE_EXCHANGE_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": self._id,
                    "client_secret": self._secret,
                    "redirect_uri": redirect_uri,
                },
            )
        except httpx.HTTPError as exc:
            raise AppError(_DENIED) from exc
        access = _token(token)
        try:
            info = await client.get(
                INFO_URL,
                params={"format": "json"},
                headers={"Authorization": f"OAuth {access}"},
            )
        except httpx.HTTPError as exc:
            raise AppError(_DENIED) from exc
        if not info.is_success:
            raise AppError(_DENIED)
        body = _object(info)
        account_id = str(body.get("id") or "").strip()
        email = str(body.get("default_email") or "").strip()
        if not account_id or not email:
            raise AppError(_DENIED)
        return YandexAccount(
            account_id=account_id[:64],
            email=email,
            first_name=str(body.get("first_name") or "").strip(),
            last_name=str(body.get("last_name") or "").strip(),
            portrait=await _portrait(client, body),
        )


def _token(response: httpx.Response) -> str:
    if not response.is_success:
        raise AppError(_DENIED)
    access = _object(response).get("access_token")
    if not isinstance(access, str) or not access:
        raise AppError(_DENIED)
    return access


def _object(response: httpx.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError as exc:
        raise AppError(_DENIED) from exc
    if not isinstance(body, dict):
        raise AppError(_DENIED)
    return body


async def _portrait(client: httpx.AsyncClient, info: dict[str, Any]) -> tuple[bytes, str] | None:
    """A real portrait only. The empty placeholder (`is_avatar_empty`) is skipped."""
    if info.get("is_avatar_empty") is True:
        return None
    raw = info.get("default_avatar_id")
    avatar_id = str(raw).strip() if raw else ""
    if not _AVATAR_ID.fullmatch(avatar_id) or ".." in avatar_id or avatar_id.startswith("/"):
        return None
    url = f"https://avatars.yandex.net/get-yapic/{avatar_id}/islands-200"
    try:
        picture = await client.get(url)
    except httpx.HTTPError:
        return None
    if not picture.is_success or len(picture.content) > PHOTO_LIMIT:
        return None
    media = sniff_image(picture.content)
    if media is None:
        return None
    return picture.content, media
