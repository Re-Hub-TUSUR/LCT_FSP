"""FSP ID (Keycloak OIDC) and the FSP participant registry. See docs/FSP_INTEGRATION.md.

`FSP_ID_MODE` picks the implementation: `mock` emulates both systems inside this API,
`keycloak` talks to the real realm and registry. The rest of the backend sees only the
`FspIdProvider` and `FspRegistryClient` protocols.
"""

from app.core.config import Settings
from app.integrations.fsp.keycloak import KeycloakFspIdProvider
from app.integrations.fsp.mock import MockFspIdProvider, MockFspRegistry
from app.integrations.fsp.provider import FspIdProvider
from app.integrations.fsp.registry import FspRegistryClient, HttpFspRegistryClient


def fsp_id_provider(settings: Settings) -> FspIdProvider:
    if settings.fsp_id_mode == "keycloak":
        return KeycloakFspIdProvider(settings)
    return MockFspIdProvider(settings)


def fsp_registry(settings: Settings) -> FspRegistryClient:
    if settings.fsp_id_mode == "keycloak":
        return HttpFspRegistryClient(settings)
    return MockFspRegistry()
