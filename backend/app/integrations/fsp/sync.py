"""Mirrors a registry record into the candidate's FSP rows."""

import logging
from datetime import UTC, datetime

from app.integrations.fsp.registry import FspRegistryClient, FspRegistryError
from app.integrations.fsp.schemas import FspMemberRecord
from app.models import CandidateProfile, FspAchievement, FspSportTitle

logger = logging.getLogger(__name__)


class FspSyncService:
    def __init__(self, registry: FspRegistryClient) -> None:
        self._registry = registry

    async def sync(self, profile: CandidateProfile) -> bool:
        """Imports the registry history. A failure keeps the link and the previous rows.

        `profile.fsp_achievements` and `profile.fsp_titles` must be loaded.
        """
        if profile.fsp_member_id is None:
            return False
        try:
            record = await self._registry.fetch_member(profile.fsp_member_id)
        except FspRegistryError as exc:
            logger.warning("FSP registry sync failed for %s: %s", profile.id, exc.message)
            profile.fsp_sync_error = exc.message
            return False
        apply_record(profile, record)
        return True


def apply_record(profile: CandidateProfile, record: FspMemberRecord) -> None:
    """Upsert by registry id: a re-sync updates rows in place and drops the vanished ones."""
    achievements = {item.external_id: item for item in profile.fsp_achievements}
    rows: list[FspAchievement] = []
    for item in record.achievements:
        row = achievements.get(item.id) or FspAchievement(external_id=item.id)
        row.event_name = item.event_name
        row.event_kind = item.event_kind
        row.discipline = item.discipline
        row.level = item.level
        row.year = item.year
        row.place = item.place
        row.result = item.result
        row.participation = item.participation
        row.team_name = item.team_name
        rows.append(row)
    profile.fsp_achievements = sorted(rows, key=lambda row: (-row.year, row.external_id))

    titles = {item.external_id: item for item in profile.fsp_titles}
    title_rows: list[FspSportTitle] = []
    for title in record.titles:
        title_row = titles.get(title.id) or FspSportTitle(external_id=title.id)
        title_row.kind = title.kind
        title_row.discipline = title.discipline
        title_row.awarded_year = title.awarded_year
        title_rows.append(title_row)
    profile.fsp_titles = sorted(title_rows, key=lambda row: (-row.awarded_year, row.external_id))

    profile.fsp_synced_at = datetime.now(UTC)
    profile.fsp_sync_error = None


def clear_fsp(profile: CandidateProfile) -> None:
    profile.fsp_achievements.clear()
    profile.fsp_titles.clear()
    profile.fsp_member_id = None
    profile.fsp_linked_at = None
    profile.fsp_synced_at = None
    profile.fsp_sync_error = None
