"""Every ATS adapter answers the same calls. Provider DTOs stay out of the domain."""

import inspect

import pytest

from app.integrations.ats.fixture.provider import FixtureAtsProvider
from app.integrations.ats.mock import MockAtsProvider
from app.integrations.ats.provider import AtsProvider
from app.services import ats as ats_service
from app.services import ats_pipeline


def _providers() -> list[AtsProvider]:
    return [MockAtsProvider(), FixtureAtsProvider()]


@pytest.mark.parametrize("provider", _providers())
async def test_poll_is_stable_for_the_same_cursor(provider: AtsProvider) -> None:
    first = await provider.poll(None)
    again = await provider.poll(None)
    assert first.changes
    assert [item.external_event_id for item in first.changes] == [
        item.external_event_id for item in again.changes
    ]
    for change in first.changes:
        assert change.application.candidate.skills
        assert change.application.job.required_skills
        assert change.raw

    done = await provider.poll(first.next_cursor)
    assert done.changes == ()
    assert done.next_cursor == first.next_cursor


@pytest.mark.parametrize("provider", _providers())
async def test_write_back_is_readable(provider: AtsProvider) -> None:
    page = await provider.poll(None)
    external_id = page.changes[0].application.external_id
    await provider.write_tag(external_id, "kadry:pass")
    await provider.write_note(external_id, "Совпали навыки: Python")
    await provider.write_score(external_id, 90)

    kinds = {record.kind: record.value for record in provider.records(external_id)}
    assert kinds == {"tag": "kadry:pass", "note": "Совпали навыки: Python", "score": "90"}


def test_domain_does_not_import_provider_dtos() -> None:
    domain = inspect.getsource(ats_service) + inspect.getsource(ats_pipeline)
    assert "FixturePerson" not in domain
    assert "FixtureOpening" not in domain
    assert "fixture.dto" not in domain
