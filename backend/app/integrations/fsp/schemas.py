"""Data contract of the FSP registry (docs/fsp-registry.openapi.yaml).

Kept apart from the ORM: the registry is mapped onto our tables by `app.integrations.fsp.sync`,
so a change on the FSP side touches only this module and the mapping.
"""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.models.enums import (
    FspDiscipline,
    FspEventKind,
    FspEventLevel,
    FspOutcome,
    FspParticipation,
    FspTitleKind,
)


class RegistryModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, validate_by_name=True, serialize_by_alias=True, frozen=True
    )


class FspRegistryAchievement(RegistryModel):
    id: str = Field(min_length=1, max_length=64)
    event_name: str = Field(min_length=1, max_length=300)
    event_kind: FspEventKind
    discipline: FspDiscipline
    level: FspEventLevel
    year: int = Field(ge=2000, le=2100)
    # Null = took part without a place.
    place: int | None = Field(default=None, gt=0)
    result: FspOutcome
    participation: FspParticipation
    team_name: str | None = Field(default=None, max_length=200)


class FspRegistryTitle(RegistryModel):
    id: str = Field(min_length=1, max_length=64)
    kind: FspTitleKind
    discipline: FspDiscipline
    awarded_year: int = Field(ge=1990, le=2100)


class FspMemberRecord(RegistryModel):
    """Everything the registry knows about one participant. Empty lists = no FSP history."""

    member_id: str = Field(min_length=1, max_length=64)
    achievements: list[FspRegistryAchievement] = Field(default_factory=list)
    titles: list[FspRegistryTitle] = Field(default_factory=list)


@dataclass(frozen=True, slots=True)
class FspIdentity:
    """Who signed in to FSP ID: claims of the verified ID token."""

    # Keycloak user id (`sub`).
    subject: str
    # Participant id in the registry (`fsp_member_id` claim, a realm user attribute).
    member_id: str
    name: str | None = None
