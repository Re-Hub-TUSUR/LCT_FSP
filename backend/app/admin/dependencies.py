from typing import Annotated

from fastapi import Depends

from app.admin.services.bank import AdminBankService
from app.admin.services.banlist import BanlistService
from app.admin.services.dictionaries import DictionaryService
from app.admin.services.employers import EmployerModerationService
from app.admin.services.parameters import ParameterService
from app.admin.services.snapshots import SnapshotService
from app.admin.services.verification import VerificationService
from app.dependencies.common import SessionDep, SettingsDep
from app.dependencies.services import AssessmentBankServiceDep, NotificationHubDep


def get_admin_bank(session: SessionDep, bank: AssessmentBankServiceDep) -> AdminBankService:
    return AdminBankService(session, bank)


def get_snapshots(session: SessionDep) -> SnapshotService:
    return SnapshotService(session)


def get_parameters(session: SessionDep) -> ParameterService:
    return ParameterService(session)


def get_dictionaries(session: SessionDep) -> DictionaryService:
    return DictionaryService(session)


def get_employer_moderation(session: SessionDep) -> EmployerModerationService:
    return EmployerModerationService(session)


def get_banlist(session: SessionDep) -> BanlistService:
    return BanlistService(session)


def get_verification(
    session: SessionDep, settings: SettingsDep, hub: NotificationHubDep
) -> VerificationService:
    return VerificationService(session, settings, hub)


AdminBankDep = Annotated[AdminBankService, Depends(get_admin_bank)]
SnapshotsDep = Annotated[SnapshotService, Depends(get_snapshots)]
ParametersDep = Annotated[ParameterService, Depends(get_parameters)]
DictionariesDep = Annotated[DictionaryService, Depends(get_dictionaries)]
EmployerModerationDep = Annotated[EmployerModerationService, Depends(get_employer_moderation)]
BanlistDep = Annotated[BanlistService, Depends(get_banlist)]
VerificationDep = Annotated[VerificationService, Depends(get_verification)]
