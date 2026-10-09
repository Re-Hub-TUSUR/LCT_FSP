import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from datetime import timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import API_PREFIX, api_router
from app.api.routes import mock_fsp
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.headers import security_headers_middleware
from app.core.logging import configure_logging, request_logging_middleware
from app.core.openapi import TAGS_METADATA, register_docs
from app.db.session import get_engine, get_sessionmaker
from app.repositories.candidate import CandidateRepository
from app.search.elastic import ElasticSearchState, create_client
from app.services.ats import run_ats_poll
from app.services.notifications import NotificationHub
from app.services.saved_searches import run_alerts

logger = logging.getLogger(__name__)


async def _prepare_search(elastic: ElasticSearchState) -> None:
    """Builds the index on the first start; failures only delay it (the API stays up)."""
    try:
        async with get_sessionmaker()() as session:
            await elastic.ready(CandidateRepository(session).all)
    except Exception:
        logger.exception("Search index preparation failed; the database search is used for now")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        elastic = None
        if settings.elasticsearch_url:
            elastic = ElasticSearchState(create_client(settings), settings.elasticsearch_index)
            app.state.elastic = elastic
            await _prepare_search(elastic)
        alerts = None
        ats_poll = None
        if settings.ats_poll_seconds:
            ats_poll = asyncio.create_task(
                run_ats_poll(
                    timedelta(seconds=settings.ats_poll_seconds),
                    get_sessionmaker(),
                    settings,
                )
            )
        if settings.saved_search_alert_minutes:
            alerts = asyncio.create_task(
                run_alerts(
                    timedelta(minutes=settings.saved_search_alert_minutes),
                    get_sessionmaker(),
                    app.state.notifications,
                    elastic,
                )
            )
        yield
        if ats_poll is not None:
            ats_poll.cancel()
            with suppress(asyncio.CancelledError):
                await ats_poll
        if alerts is not None:
            alerts.cancel()
            with suppress(asyncio.CancelledError):
                await alerts
        if elastic is not None:
            await elastic.close()
        await get_engine().dispose()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="API платформы подбора ИТ-специалистов ФСП. Ошибки: `{error: {code, message}}`",
        # The Swagger UI route is registered by hand below, with its own CSP.
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/openapi.json",
        openapi_tags=TAGS_METADATA,
        lifespan=lifespan,
    )
    register_docs(app, docs_url="/api/docs", openapi_url="/api/openapi.json")

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "Accept", "X-Kadry-Request"],
        )
    app.middleware("http")(security_headers_middleware)
    app.middleware("http")(request_logging_middleware)
    register_exception_handlers(app)
    app.state.notifications = NotificationHub()
    app.include_router(api_router)
    if settings.fsp_id_mode == "mock":
        app.include_router(mock_fsp.router, prefix=API_PREFIX)
    return app


app = create_app()
