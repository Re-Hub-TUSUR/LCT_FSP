from typing import Annotated

from fastapi import Depends, Request

from app.dependencies.common import SessionDep, SettingsDep
from app.repositories.assessment import AssessmentRepository
from app.repositories.candidate import CandidateRepository
from app.repositories.company import CompanyRepository
from app.repositories.email_verification import EmailVerificationRepository
from app.repositories.invitation import InvitationRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.inbound import InboundRepository
from app.repositories.meeting import MeetingRepository
from app.repositories.reaction import ReactionRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.repositories.vacancy import VacancyRepository
from app.search.elastic import ElasticSearchState
from app.services.assessment_bank import AssessmentBankService
from app.services.assessments import AssessmentService
from app.services.auth import AuthService
from app.services.calendar import CalendarService
from app.services.candidate_search import CandidateSearchService
from app.services.candidates import CandidateProfileService
from app.services.code_runner import CodeRunner, OnlineCompilerRunner
from app.services.email import ResendEmailSender
from app.services.chat import ChatService
from app.services.notifications import NotificationHub
from app.services.reactions import ReactionService
from app.services.responses import ResponsesService
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


def get_notification_hub(request: Request) -> NotificationHub:
    return request.app.state.notifications


NotificationHubDep = Annotated[NotificationHub, Depends(get_notification_hub)]


def get_reaction_service(
    session: SessionDep, hub: NotificationHubDep
) -> ReactionService:
    return ReactionService(
        ReactionRepository(session),
        VacancyRepository(session),
        CandidateRepository(session),
        CompanyRepository(session),
        hub,
    )


ReactionServiceDep = Annotated[ReactionService, Depends(get_reaction_service)]


def get_responses_service(
    session: SessionDep, reactions: ReactionServiceDep
) -> ResponsesService:
    return ResponsesService(
        InboundRepository(session),
        reactions,
        CompanyRepository(session),
    )


ResponsesServiceDep = Annotated[ResponsesService, Depends(get_responses_service)]


def get_chat_service(session: SessionDep, hub: NotificationHubDep, settings: SettingsDep) -> ChatService:
    return ChatService(
        ConversationRepository(session),
        ReactionRepository(session),
        CompanyRepository(session),
        CandidateRepository(session),
        VacancyRepository(session),
        MeetingRepository(session),
        settings,
        hub,
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


def get_assessment_service(
    session: SessionDep, runner: CodeRunnerDep, settings: SettingsDep
) -> AssessmentService:
    return AssessmentService(
        AssessmentRepository(session), CandidateRepository(session), runner, settings
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


def get_assessment_bank_service(
    session: SessionDep, runner: CodeRunnerDep
) -> AssessmentBankService:
    return AssessmentBankService(AssessmentRepository(session), runner)


AssessmentBankServiceDep = Annotated[AssessmentBankService, Depends(get_assessment_bank_service)]
