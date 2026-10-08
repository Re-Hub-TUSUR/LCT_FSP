"""FSP ID: the federation's Keycloak realm, used to link a profile (not to sign in).

Authorization code flow with PKCE (RFC 7636). The `fsp_member_id` claim of the ID token names
the participant in the registry. `MockFspIdProvider` emulates the realm for the hackathon,
`KeycloakFspIdProvider` talks to the real one; both satisfy `FspIdProvider`.
"""

import base64
import hashlib
import ipaddress
from typing import Any, Protocol
from urllib.parse import urlencode, urlsplit

from app.core.config import Settings
from app.core.errors import AppError
from app.integrations.fsp.schemas import FspIdentity

SCOPES = "openid profile fsp-profile"
MEMBER_CLAIM = "fsp_member_id"
CALLBACK_PATH = "/profile/fsp/callback"
# Width of `candidate_profiles.fsp_member_id`.
MAX_MEMBER_ID = 64


class FspIdError(AppError):
    code = "fsp_id_failed"
    default_message = "Не удалось подтвердить вход через ФСП ID. Попробуйте ещё раз."


class FspIdProvider(Protocol):
    def authorize_url(
        self, *, state: str, nonce: str, code_challenge: str, redirect_uri: str
    ) -> str: ...

    async def exchange_code(
        self, *, code: str, code_verifier: str, redirect_uri: str, nonce: str
    ) -> FspIdentity: ...


def code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def authorize_url(
    settings: Settings, *, state: str, nonce: str, code_challenge: str, redirect_uri: str
) -> str:
    """Keycloak's authorization endpoint with the standard OIDC parameters."""
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.fsp_id_client_id,
            "redirect_uri": redirect_uri,
            "scope": SCOPES,
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{settings.fsp_id_issuer.rstrip('/')}/protocol/openid-connect/auth?{query}"


def redirect_allowed(settings: Settings, redirect_uri: str) -> bool:
    """The configured callback, or the same page on one of the trusted SPA origins.

    The emulated realm also accepts the page on this machine or its local network, on any port:
    a demo opened through Docker or by IP links without extra configuration.
    """
    if redirect_uri == settings.fsp_id_redirect_uri:
        return True
    parts = urlsplit(redirect_uri)
    if parts.path != CALLBACK_PATH or parts.query or parts.fragment:
        return False
    if f"{parts.scheme}://{parts.netloc}" in settings.cors_origins:
        return True
    return (
        settings.fsp_id_mode == "mock"
        and parts.scheme in ("http", "https")
        and _is_local(parts.hostname)
    )


def _is_local(host: str | None) -> bool:
    if host is None:
        return False
    if host == "localhost":
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return address.is_loopback or address.is_private


def identity_from_claims(claims: dict[str, Any], *, settings: Settings, nonce: str) -> FspIdentity:
    """Checks of OIDC Core 3.1.3.7 that do not depend on how the signature was verified."""
    audience = claims.get("aud")
    audiences = audience if isinstance(audience, list) else [audience]
    if claims.get("iss") != settings.fsp_id_issuer.rstrip("/"):
        raise FspIdError("ФСП ID: токен выдан другим сервером")
    if settings.fsp_id_client_id not in audiences:
        raise FspIdError("ФСП ID: токен выдан другому приложению")
    if claims.get("nonce") != nonce:
        raise FspIdError("ФСП ID: ответ не относится к этому входу")
    member_id = claims.get(MEMBER_CLAIM)
    if not isinstance(member_id, str) or not member_id.strip() or len(member_id) > MAX_MEMBER_ID:
        raise FspIdError("В профиле ФСП ID нет номера участника")
    name = claims.get("name")
    return FspIdentity(
        subject=str(claims.get("sub", "")),
        member_id=member_id.strip(),
        name=name if isinstance(name, str) else None,
    )
