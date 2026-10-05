from typing import Annotated

from fastapi import Depends

from app.dependencies.common import SessionDep, SettingsDep
from app.repositories.email_verification import EmailVerificationRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
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
