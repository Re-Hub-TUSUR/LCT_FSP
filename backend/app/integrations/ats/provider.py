"""The only surface the rest of the backend uses to talk to an ATS."""

from typing import Protocol

from app.integrations.ats.normalized import AtsRecord, PollPage


class AtsProvider(Protocol):
    name: str

    async def poll(self, cursor: str | None) -> PollPage:
        """Applications changed since `cursor`. The same cursor returns the same events."""

    async def write_tag(self, external_application_id: str, tag: str) -> None: ...

    async def write_note(self, external_application_id: str, note: str) -> None: ...

    async def write_score(self, external_application_id: str, score: int) -> None: ...

    def records(self, external_application_id: str) -> tuple[AtsRecord, ...]:
        """What this provider stored for the application. Empty until a write."""
