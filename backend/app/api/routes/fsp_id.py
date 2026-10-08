from fastapi import APIRouter

from app.dependencies.auth import CandidateUser
from app.dependencies.services import FspLinkServiceDep
from app.schemas.candidate import FspAuthorizeRead, FspAuthorizeRequest

router = APIRouter(prefix="/fsp-id", tags=["fsp-id"])


@router.post(
    "/authorize",
    summary="Start linking FSP ID: the sign-in URL to send the browser to",
    description=(
        "OIDC authorization code flow with PKCE (Keycloak). FSP ID returns the browser to "
        "`redirectUri` with `code` and `state`; pass them to `POST /candidates/me/fsp-link`."
    ),
)
async def authorize(
    user: CandidateUser, data: FspAuthorizeRequest, fsp: FspLinkServiceDep
) -> FspAuthorizeRead:
    return await fsp.authorize(user, data.redirect_uri)
