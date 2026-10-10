"""The real FSP ID realm (Keycloak). Enabled with `FSP_ID_MODE=keycloak`."""

import logging
from typing import Any

import jwt

from app.core.config import Settings
from app.integrations.fsp import provider
from app.integrations.fsp.http import HttpCallError, post_form
from app.integrations.fsp.provider import FspIdError
from app.integrations.fsp.schemas import FspIdentity

logger = logging.getLogger(__name__)


class KeycloakFspIdProvider:
    """Confidential client: the code is exchanged with the client secret and the PKCE verifier.

    The ID token comes straight from the token endpoint over TLS, so its issuer is proven by
    the TLS certificate and the signature check is optional (OIDC Core 3.1.3.7, item 6). Claims
    are still validated; verifying the RS256 signature against the realm JWKS needs
    `pyjwt[crypto]` and is listed in docs/FSP_INTEGRATION.md as a production step.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        issuer = settings.fsp_id_issuer.rstrip("/")
        # The unsigned check above rests on TLS: a plain-HTTP token endpoint would let anyone
        # on the way hand us any identity.
        if settings.is_production and not issuer.startswith("https://"):
            msg = "FSP_ID_ISSUER must be an https:// URL in production"
            raise ValueError(msg)
        self._token_url = f"{issuer}/protocol/openid-connect/token"

    def authorize_url(
        self, *, state: str, nonce: str, code_challenge: str, redirect_uri: str
    ) -> str:
        return provider.authorize_url(
            self._settings,
            state=state,
            nonce=nonce,
            code_challenge=code_challenge,
            redirect_uri=redirect_uri,
        )

    async def exchange_code(
        self, *, code: str, code_verifier: str, redirect_uri: str, nonce: str
    ) -> FspIdentity:
        try:
            tokens = await post_form(
                self._token_url,
                {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self._settings.fsp_id_client_id,
                    "client_secret": self._settings.fsp_id_client_secret.get_secret_value(),
                    "code_verifier": code_verifier,
                },
            )
        except HttpCallError as exc:
            logger.warning("FSP ID token exchange failed: %s", exc)
            raise FspIdError() from exc
        return provider.identity_from_claims(
            _id_token_claims(tokens), settings=self._settings, nonce=nonce
        )


def _id_token_claims(tokens: dict[str, Any]) -> dict[str, Any]:
    id_token = tokens.get("id_token")
    if not isinstance(id_token, str):
        raise FspIdError("ФСП ID не вернул ID-токен")
    try:
        claims: dict[str, Any] = jwt.decode(
            id_token,
            options={
                "verify_signature": False,
                "verify_exp": True,
                "require": ["exp", "iat", "sub", "iss", "aud"],
            },
        )
    except jwt.InvalidTokenError as exc:
        raise FspIdError("ФСП ID вернул некорректный ID-токен") from exc
    return claims
