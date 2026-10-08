from typing import Annotated

from fastapi import Depends, Request

from app.dependencies.common import SessionDep, SettingsDep
from app.integrations.fsp import fsp_id_provider, fsp_registry
from app.integrations.fsp.provider import FspIdProvider
from app.integrations.fsp.registry import FspRegistryClient
from app.integrations.fsp.sync import FspSyncService
from app.repositories.assessment import AssessmentRepository
from app.repositories.candidate import CandidateRepository
from app.repositories.company import CompanyRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.email_verification import EmailVerificationRepository
from app.repositories.inbound import InboundRepository
from app.repositories.invitation import InvitationRepository
from app.repositories.meeting import MeetingRepository
from app.repositories.reaction import ReactionRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.repositories.vacancy import VacancyRepository
from app.search.elastic import ElasticSearchState
from app.services.assessment_bank import AssessmentBankService
from app.services.assessments import AssessmentService
from app.services.attempt_context import AttemptContextService
from app.services.auth import AuthService
from app.services.calendar import CalendarService
from app.services.candidate_search import CandidateSearchService
from app.services.candidates import CandidateProfileService
from app.services.chat import ChatService
from app.services.code_runner import CodeRunner, OnlineCompilerRunner
from app.services.email import ResendEmailSender
from app.services.fsp_link import FspLinkService
from app.services.interview import AttemptInterviewService, Interviewer
from app.services.llm import RouterAiModel
from app.services.notifications import NotificationHub
from app.services.reactions import ReactionService
from app.services.responses import ResponsesService
from app.services.resume_import import ResumeImportService
from app.services.resume_reader import LlmResumeReader, ResumeReader
from app.services.test_assignments import TestAssignmentService
from app.services.vacancies import VacancyService
from app.services.vacancy_feed import VacancyFeedService


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_auth_service(
    session: SessionDep, users: UserRepositoryDep, settings: SettingsDep
) -> AuthService:
    return AuthService(
        users,
        EmailVerificationRepository(session),
        RefreshTokenRepository(session),
        settings,
        ResendEmailSender(settings),
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_vacancy_service(session: SessionDep) -> VacancyService:
    return VacancyService(VacancyRepository(session), CompanyRepository(session))


VacancyServiceDep = Annotated[VacancyService, Depends(get_vacancy_service)]


def get_vacancy_feed_service(session: SessionDep) -> VacancyFeedService:
    return VacancyFeedService(
        VacancyRepository(session), CandidateRepository(session), ReactionRepository(session)
    )


VacancyFeedServiceDep = Annotated[VacancyFeedService, Depends(get_vacancy_feed_service)]


def get_candidate_search_service(request: Request, session: SessionDep) -> CandidateSearchService:
    # Set by the app lifespan when ELASTICSEARCH_URL is configured; otherwise the database answers.
    elastic: ElasticSearchState | None = getattr(request.app.state, "elastic", None)
    return CandidateSearchService(
        CandidateRepository(session),
        VacancyRepository(session),
        CompanyRepository(session),
        ReactionRepository(session),
        elastic,
    )


CandidateSearchServiceDep = Annotated[CandidateSearchService, Depends(get_candidate_search_service)]


def get_candidate_profile_service(session: SessionDep) -> CandidateProfileService:
    return CandidateProfileService(
        CandidateRepository(session),
        InvitationRepository(session),
        ReactionRepository(session),
        CompanyRepository(session),
    )


CandidateProfileServiceDep = Annotated[
    CandidateProfileService, Depends(get_candidate_profile_service)
]


def get_fsp_id_provider(settings: SettingsDep) -> FspIdProvider:
    return fsp_id_provider(settings)


def get_fsp_registry(settings: SettingsDep) -> FspRegistryClient:
    return fsp_registry(settings)


def get_fsp_link_service(
    session: SessionDep,
    settings: SettingsDep,
    provider: Annotated[FspIdProvider, Depends(get_fsp_id_provider)],
    registry: Annotated[FspRegistryClient, Depends(get_fsp_registry)],
) -> FspLinkService:
    return FspLinkService(
        CandidateRepository(session), provider, FspSyncService(registry), settings
    )


FspLinkServiceDep = Annotated[FspLinkService, Depends(get_fsp_link_service)]


def get_notification_hub(request: Request) -> NotificationHub:
    hub: NotificationHub = request.app.state.notifications
    return hub


NotificationHubDep = Annotated[NotificationHub, Depends(get_notification_hub)]


def get_reaction_service(session: SessionDep, hub: NotificationHubDep) -> ReactionService:
    return ReactionService(
        ReactionRepository(session),
        VacancyRepository(session),
        CandidateRepository(session),
        CompanyRepository(session),
        hub,
    )


ReactionServiceDep = Annotated[ReactionService, Depends(get_reaction_service)]


def get_responses_service(session: SessionDep, reactions: ReactionServiceDep) -> ResponsesService:
    return ResponsesService(
        InboundRepository(session),
        reactions,
        CompanyRepository(session),
    )


ResponsesServiceDep = Annotated[ResponsesService, Depends(get_responses_service)]


def get_chat_service(
    session: SessionDep, hub: NotificationHubDep, settings: SettingsDep
) -> ChatService:
    return ChatService(
        conversations=ConversationRepository(session),
        reactions=ReactionRepository(session),
        companies=CompanyRepository(session),
        candidates=CandidateRepository(session),
        vacancies=VacancyRepository(session),
        meetings=MeetingRepository(session),
        settings=settings,
        notifications=hub,
    )


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]


def get_calendar_service(session: SessionDep) -> CalendarService:
    return CalendarService(
        MeetingRepository(session),
        CompanyRepository(session),
        CandidateRepository(session),
        VacancyRepository(session),
    )


CalendarServiceDep = Annotated[CalendarService, Depends(get_calendar_service)]


def get_code_runner(settings: SettingsDep) -> CodeRunner:
    return OnlineCompilerRunner(settings)


CodeRunnerDep = Annotated[CodeRunner, Depends(get_code_runner)]


def get_resume_reader(settings: SettingsDep) -> ResumeReader:
    return LlmResumeReader(RouterAiModel(settings, settings.resume_parser_model))


ResumeReaderDep = Annotated[ResumeReader, Depends(get_resume_reader)]


def get_resume_import_service(reader: ResumeReaderDep) -> ResumeImportService:
    return ResumeImportService(reader)


ResumeImportServiceDep = Annotated[ResumeImportService, Depends(get_resume_import_service)]


def get_interviewer(settings: SettingsDep) -> Interviewer:
    return Interviewer(RouterAiModel(settings, settings.interview_model), settings.interview_model)


InterviewerDep = Annotated[Interviewer, Depends(get_interviewer)]


def get_assessment_service(
    session: SessionDep, runner: CodeRunnerDep, settings: SettingsDep, interviewer: InterviewerDep
) -> AssessmentService:
    return AssessmentService(
        AssessmentRepository(session),
        CandidateRepository(session),
        runner,
        settings,
        interviews=interviewer.available,
    )


AssessmentServiceDep = Annotated[AssessmentService, Depends(get_assessment_service)]


def get_test_assignment_service(
    session: SessionDep, assessments: AssessmentServiceDep
) -> TestAssignmentService:
    return TestAssignmentService(
        AssessmentRepository(session),
        CompanyRepository(session),
        CandidateRepository(session),
        vacancies=VacancyRepository(session),
        reactions=ReactionRepository(session),
        assessments=assessments,
    )


TestAssignmentServiceDep = Annotated[TestAssignmentService, Depends(get_test_assignment_service)]


def get_attempt_context_service(session: SessionDep) -> AttemptContextService:
    return AttemptContextService(AssessmentRepository(session))


AttemptContextServiceDep = Annotated[AttemptContextService, Depends(get_attempt_context_service)]


def get_attempt_interview_service(
    session: SessionDep,
    contexts: AttemptContextServiceDep,
    assessments: AssessmentServiceDep,
    interviewer: InterviewerDep,
    settings: SettingsDep,
) -> AttemptInterviewService:
    return AttemptInterviewService(
        repository=AssessmentRepository(session),
        candidates=CandidateRepository(session),
        contexts=contexts,
        assessments=assessments,
        interviewer=interviewer,
        settings=settings,
    )


AttemptInterviewServiceDep = Annotated[
    AttemptInterviewService, Depends(get_attempt_interview_service)
]


def get_assessment_bank_service(
    session: SessionDep, runner: CodeRunnerDep
) -> AssessmentBankService:
    return AssessmentBankService(AssessmentRepository(session), runner)


AssessmentBankServiceDep = Annotated[AssessmentBankService, Depends(get_assessment_bank_service)]
