"""Poll an ATS, screen with our pipeline, write the decision back.

The provider and the pipeline are arguments, so a new ATS or a new scorer
does not change this module's control flow.
"""

import asyncio
import logging
from dataclasses import replace
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.errors import NotFoundError
from app.integrations.ats import ats_provider
from app.integrations.ats.normalized import NormalizedCandidate, NormalizedJob, PollChange
from app.integrations.ats.provider import AtsProvider
from app.models import Company, User
from app.models.ats import AtsApplication, AtsConnection, ScreeningResult
from app.models.enums import AtsSyncKind
from app.repositories.ats import AtsRepository
from app.repositories.company import CompanyRepository
from app.schemas.ats import AtsApplicationRead, AtsConnectionRead, AtsPollRead
from app.services.ats_pipeline import ScreeningPipeline, ScreeningState, default_pipeline
from app.services.resume_text import ResumeFileError, read_resume

logger = logging.getLogger(__name__)


class AtsService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        provider: AtsProvider | None = None,
        pipeline: ScreeningPipeline | None = None,
    ) -> None:
        self._session = session
        self._settings = settings
        self._provider = provider if provider is not None else ats_provider(settings)
        self._pipeline = pipeline if pipeline is not None else default_pipeline()
        self._ats = AtsRepository(session)
        self._companies = CompanyRepository(session)

    async def read_connection(self, user: User) -> AtsConnectionRead:
        company = await self._require_company(user)
        connection = await self._ats.connection_for_company(company.id)
        if connection is None:
            return AtsConnectionRead(connected=False, provider=None, cursor=None)
        return AtsConnectionRead(
            connected=True, provider=connection.provider, cursor=connection.cursor
        )

    async def connect(self, user: User) -> AtsConnectionRead:
        company = await self._require_company(user)
        connection = await self._ats.connection_for_company(company.id)
        if connection is None:
            connection = await self._ats.add_connection(company.id, self._provider.name)
        return AtsConnectionRead(
            connected=True, provider=connection.provider, cursor=connection.cursor
        )

    async def poll(self, user: User) -> AtsPollRead:
        company = await self._require_company(user)
        connection = await self._ats.connection_for_company(company.id)
        if connection is None:
            raise NotFoundError("Сначала подключите ATS")
        queued, screened = await self._poll_connection(connection)
        return AtsPollRead(ingested=queued, screened=screened)

    async def list_applications(self, user: User) -> list[AtsApplicationRead]:
        company = await self._require_company(user)
        connection = await self._ats.connection_for_company(company.id)
        if connection is None:
            return []
        rows = await self._ats.list_applications(connection.id)
        ids = [row.id for row in rows]
        results = await self._ats.latest_results(ids)
        synced = await self._ats.sync_kinds(ids)
        return [_read(row, results.get(row.id), synced.get(row.id, set())) for row in rows]

    async def poll_everyone(self) -> int:
        screened = 0
        for connection in await self._ats.all_connections():
            if connection.provider != self._provider.name:
                continue
            _, done = await self._poll_connection(connection)
            screened += done
        return screened

    async def _poll_connection(self, connection: AtsConnection) -> tuple[int, int]:
        page = await self._provider.poll(connection.cursor)
        queued = 0
        for change in page.changes:
            if await self._ats.take_new(connection, await _with_text(change)):
                queued += 1
        connection.cursor = page.next_cursor
        screened = await self._drain(connection)
        return queued, screened

    async def _drain(self, connection: AtsConnection) -> int:
        done = 0
        for application in await self._ats.claim_queued(connection.id):
            try:
                state = self._pipeline.run(_candidate(application), _job(application))
                sync = await self._write_back(application.external_id, state)
                await self._ats.finish(
                    application,
                    score=state.score,
                    decision=state.decision,
                    reasons=state.reasons,
                    matched_skills=state.matched_skills,
                    missing_skills=state.missing_skills,
                    model_version=state.model_version,
                    sync=sync,
                )
                done += 1
            except Exception:
                logger.exception("ATS screening failed for %s", application.id)
                await self._ats.fail(application.id)
        return done

    async def _write_back(
        self, external_id: str, state: ScreeningState
    ) -> list[tuple[AtsSyncKind, str]]:
        tag = f"kadry:{state.decision.value}"
        note = "; ".join(state.reasons) or state.decision.value
        await self._provider.write_tag(external_id, tag)
        await self._provider.write_note(external_id, note)
        await self._provider.write_score(external_id, state.score)
        return [
            (AtsSyncKind.TAG, tag),
            (AtsSyncKind.NOTE, note),
            (AtsSyncKind.SCORE, str(state.score)),
        ]

    async def _require_company(self, user: User) -> Company:
        company = await self._companies.get_by_owner(user.id)
        if company is None:
            raise NotFoundError("Сначала заполните профиль компании")
        return company


def _candidate(application: AtsApplication) -> NormalizedCandidate:
    person = application.candidate
    return NormalizedCandidate(
        external_id=person.external_id,
        name=person.name,
        skills=tuple(person.skills),
        experience_years=person.experience_years,
        city=person.city,
        salary_expectation=person.salary_expectation,
        resume_text=person.resume_text,
    )


def _job(application: AtsApplication) -> NormalizedJob:
    job = application.job
    return NormalizedJob(
        external_id=job.external_id,
        title=job.title,
        required_skills=tuple(job.required_skills),
        salary_from=job.salary_from,
        salary_to=job.salary_to,
        city=job.city,
    )


def _read(
    row: AtsApplication,
    result: ScreeningResult | None,
    kinds: set[AtsSyncKind],
) -> AtsApplicationRead:
    complete = {AtsSyncKind.TAG, AtsSyncKind.NOTE, AtsSyncKind.SCORE} <= kinds
    return AtsApplicationRead(
        id=row.id,
        external_id=row.external_id,
        candidate_name=row.candidate.name,
        job_title=row.job.title,
        city=row.candidate.city,
        score=None if result is None else result.score,
        decision=None if result is None else result.decision.value,
        reasons=[] if result is None else list(result.reasons),
        matched_skills=[] if result is None else list(result.matched_skills),
        missing_skills=[] if result is None else list(result.missing_skills),
        model_version=None if result is None else result.model_version,
        synced=complete,
    )


async def _with_text(change: PollChange) -> PollChange:
    person = change.application.candidate
    if person.resume_text or not person.resume_bytes:
        return change
    try:
        document = await asyncio.to_thread(read_resume, person.resume_bytes)
    except ResumeFileError:
        return change
    candidate = replace(person, resume_text=document.text, resume_bytes=None)
    return replace(change, application=replace(change.application, candidate=candidate))


async def run_ats_poll(
    interval: timedelta,
    sessions: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    """Polls every connected employer until cancelled. `interval` 0 keeps this off."""
    while True:
        await asyncio.sleep(interval.total_seconds())
        try:
            async with sessions() as session:
                await AtsService(session, settings).poll_everyone()
                await session.commit()
        except Exception:
            logger.exception("ATS poll failed; the next pass tries again")
