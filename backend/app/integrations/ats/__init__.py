"""ATS connector. The domain sees `AtsProvider` and the normalized models only.

`ATS_MODE=mock` uses the in-process demo. `fixture` reads a JSON file with a different
field names, to prove a second provider plugs in without touching the pipeline.
A live ATS later is another module registered here.
"""

from app.core.config import Settings
from app.integrations.ats.fixture.provider import FixtureAtsProvider
from app.integrations.ats.mock import MockAtsProvider
from app.integrations.ats.provider import AtsProvider


def ats_provider(settings: Settings) -> AtsProvider:
    if settings.ats_mode == "fixture":
        return FixtureAtsProvider()
    return MockAtsProvider()
