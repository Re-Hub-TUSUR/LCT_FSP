from typing import Annotated

from fastapi import Depends

from app.dependencies.common import SessionDep, SettingsDep
from app.repositories.assessment import AssessmentRepository
from app.repositories.candidate import CandidateRepository
from app.repositories.email_verification import EmailVerificationRepository
from app.repositories.user import UserRepository
from app.services.assessment_bank import AssessmentBankService
from app.services.assessments import AssessmentService
from app.services.auth import AuthService
from app.services.code_runner import CodeRunner, OnlineCompilerRunner
from app.services.email import ResendEmailSender


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_auth_service(
    session: SessionDep, users: UserRepositoryDep, settings: SettingsDep
) -> AuthService:
    return AuthService(
        users, EmailVerificationRepository(session), settings, ResendEmailSender(settings)
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


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


def get_assessment_bank_service(
    session: SessionDep, runner: CodeRunnerDep
) -> AssessmentBankService:
    return AssessmentBankService(AssessmentRepository(session), runner)


AssessmentBankServiceDep = Annotated[AssessmentBankService, Depends(get_assessment_bank_service)]
