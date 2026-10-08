import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.integrations.ats.normalized import NormalizedApplication, PollChange
from app.models.ats import (
    AtsApplication,
    AtsCandidate,
    AtsConnection,
    AtsJob,
    AtsRawEvent,
    AtsSyncLog,
    ScreeningJob,
    ScreeningResult,
)
from app.models.enums import AtsSyncKind, ScreeningDecision, ScreeningJobStatus


class AtsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def connection_for_company(self, company_id: uuid.UUID) -> AtsConnection | None:
        result = await self._session.execute(
            select(AtsConnection).where(AtsConnection.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def add_connection(self, company_id: uuid.UUID, provider: str) -> AtsConnection:
        connection = AtsConnection(company_id=company_id, provider=provider, cursor=None)
        self._session.add(connection)
        await self._session.flush()
        return connection

    async def all_connections(self) -> list[AtsConnection]:
        result = await self._session.execute(select(AtsConnection))
        return list(result.scalars())

    async def take_new(self, connection: AtsConnection, change: PollChange) -> bool:
        """True when the event is new and a screening job was queued."""
        event = AtsRawEvent(
            connection_id=connection.id,
            provider=connection.provider,
            external_event_id=change.external_event_id,
            payload=change.raw,
            application_id=None,
            created_at=datetime.now(UTC),
        )
        try:
            async with self._session.begin_nested():
                self._session.add(event)
                await self._session.flush()
        except IntegrityError:
            return False

        application = await self._application(connection, change.application)
        event.application_id = application.id
        queued = await self._session.execute(
            select(ScreeningJob.id).where(ScreeningJob.application_id == application.id)
        )
        if queued.scalar_one_or_none() is not None:
            await self._session.flush()
            return False
        self._session.add(
            ScreeningJob(
                application_id=application.id,
                status=ScreeningJobStatus.QUEUED,
                attempts=0,
            )
        )
        await self._session.flush()
        return True

    async def claim_queued(self, connection_id: uuid.UUID) -> list[AtsApplication]:
        result = await self._session.execute(
            select(AtsApplication)
            .join(ScreeningJob, ScreeningJob.application_id == AtsApplication.id)
            .where(
                AtsApplication.connection_id == connection_id,
                ScreeningJob.status == ScreeningJobStatus.QUEUED,
            )
            .options(
                selectinload(AtsApplication.candidate),
                selectinload(AtsApplication.job),
            )
        )
        applications = list(result.scalars())
        if not applications:
            return []
        jobs = await self._session.execute(
            select(ScreeningJob).where(
                ScreeningJob.application_id.in_([item.id for item in applications])
            )
        )
        for job in jobs.scalars():
            job.status = ScreeningJobStatus.RUNNING
            job.attempts += 1
        await self._session.flush()
        return applications

    async def finish(
        self,
        application: AtsApplication,
        *,
        score: int,
        decision: ScreeningDecision,
        reasons: list[str],
        matched_skills: list[str],
        missing_skills: list[str],
        model_version: str,
        sync: list[tuple[AtsSyncKind, str]],
    ) -> None:
        self._session.add(
            ScreeningResult(
                application_id=application.id,
                score=score,
                decision=decision,
                reasons=reasons,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                model_version=model_version,
                created_at=datetime.now(UTC),
            )
        )
        now = datetime.now(UTC)
        for kind, value in sync:
            self._session.add(
                AtsSyncLog(
                    application_id=application.id,
                    kind=kind,
                    value=value,
                    created_at=now,
                )
            )
        job = await self._session.execute(
            select(ScreeningJob).where(ScreeningJob.application_id == application.id)
        )
        row = job.scalar_one()
        row.status = ScreeningJobStatus.DONE
        await self._session.flush()

    async def fail(self, application_id: uuid.UUID) -> None:
        job = await self._session.execute(
            select(ScreeningJob).where(ScreeningJob.application_id == application_id)
        )
        row = job.scalar_one()
        row.status = ScreeningJobStatus.FAILED
        await self._session.flush()

    async def list_applications(self, connection_id: uuid.UUID) -> list[AtsApplication]:
        result = await self._session.execute(
            select(AtsApplication)
            .where(AtsApplication.connection_id == connection_id)
            .options(
                selectinload(AtsApplication.candidate),
                selectinload(AtsApplication.job),
            )
            .order_by(AtsApplication.created_at)
        )
        return list(result.scalars())

    async def latest_results(
        self, application_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, ScreeningResult]:
        if not application_ids:
            return {}
        result = await self._session.execute(
            select(ScreeningResult)
            .where(ScreeningResult.application_id.in_(application_ids))
            .order_by(ScreeningResult.created_at)
        )
        latest: dict[uuid.UUID, ScreeningResult] = {}
        for row in result.scalars():
            latest[row.application_id] = row
        return latest

    async def sync_kinds(
        self, application_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, set[AtsSyncKind]]:
        if not application_ids:
            return {}
        result = await self._session.execute(
            select(AtsSyncLog).where(AtsSyncLog.application_id.in_(application_ids))
        )
        grouped: dict[uuid.UUID, set[AtsSyncKind]] = {}
        for row in result.scalars():
            grouped.setdefault(row.application_id, set()).add(row.kind)
        return grouped

    async def _application(
        self, connection: AtsConnection, incoming: NormalizedApplication
    ) -> AtsApplication:
        existing = await self._session.execute(
            select(AtsApplication).where(
                AtsApplication.connection_id == connection.id,
                AtsApplication.external_id == incoming.external_id,
            )
        )
        found = existing.scalar_one_or_none()
        if found is not None:
            return found
        job = await self._job(connection.id, incoming)
        candidate = await self._candidate(connection.id, incoming)
        application = AtsApplication(
            connection_id=connection.id,
            job_id=job.id,
            candidate_id=candidate.id,
            external_id=incoming.external_id,
        )
        self._session.add(application)
        await self._session.flush()
        application.job = job
        application.candidate = candidate
        return application

    async def _job(self, connection_id: uuid.UUID, incoming: NormalizedApplication) -> AtsJob:
        job = incoming.job
        existing = await self._session.execute(
            select(AtsJob).where(
                AtsJob.connection_id == connection_id, AtsJob.external_id == job.external_id
            )
        )
        found = existing.scalar_one_or_none()
        if found is not None:
            return found
        row = AtsJob(
            connection_id=connection_id,
            external_id=job.external_id,
            title=job.title[:200],
            required_skills=list(job.required_skills),
            salary_from=job.salary_from,
            salary_to=job.salary_to,
            city=job.city,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def _candidate(
        self, connection_id: uuid.UUID, incoming: NormalizedApplication
    ) -> AtsCandidate:
        person = incoming.candidate
        existing = await self._session.execute(
            select(AtsCandidate).where(
                AtsCandidate.connection_id == connection_id,
                AtsCandidate.external_id == person.external_id,
            )
        )
        found = existing.scalar_one_or_none()
        if found is not None:
            return found
        row = AtsCandidate(
            connection_id=connection_id,
            external_id=person.external_id,
            name=person.name[:200],
            skills=list(person.skills),
            experience_years=person.experience_years,
            city=person.city,
            salary_expectation=person.salary_expectation,
            resume_text=person.resume_text,
        )
        self._session.add(row)
        await self._session.flush()
        return row
