"""Emulated FSP ID realm and FSP registry (`FSP_ID_MODE=mock`).

The organisers give no access to the real systems, so both run inside this API and keep their
real contracts: Keycloak's endpoint paths, the authorization code + PKCE exchange, the ID token
claims, and the registry record of docs/fsp-registry.openapi.yaml. Switching to the real
systems changes configuration only.

Tokens are HS256 JWTs signed with a key derived from `JWT_SECRET`; our own access tokens carry
another issuer and type, so neither kind is accepted in place of the other.
"""

import hashlib
import random
import secrets
import uuid
import zlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any, Final

import jwt

from app.core.config import Settings
from app.integrations.fsp import provider
from app.integrations.fsp.provider import MEMBER_CLAIM, SCOPES, FspIdError
from app.integrations.fsp.registry import FspRegistryError
from app.integrations.fsp.schemas import (
    FspIdentity,
    FspMemberRecord,
    FspRegistryAchievement,
    FspRegistryTitle,
)
from app.models.enums import (
    FspDiscipline,
    FspEventKind,
    FspEventLevel,
    FspOutcome,
    FspParticipation,
    FspTitleKind,
)
from app.seed import content
from app.seed.fixtures import CandidateFixture, load_seed_data

CODE_TTL: Final = timedelta(minutes=2)
TOKEN_TTL: Final = timedelta(minutes=5)
_ALGORITHM: Final = "HS256"
_CODE_TYPE: Final = "fsp_mock_code"
_ACCESS_TYPE: Final = "fsp_mock_access"
_SUBJECTS: Final = uuid.UUID("0b7d3c52-5f0e-4f7a-9a43-2d1f8f6c9e11")

# Participants the demo sign-in page offers. Any other id works too: its history is generated.
NO_HISTORY_ID: Final = "FSP-000000"
REGISTRY_DOWN_ID: Final = "FSP-000503"
# One password for every demo account, the same as the platform demo.
DEMO_PASSWORD: Final = "kadry-demo-2026"  # noqa: S105 - documented password of demo accounts


@dataclass(frozen=True, slots=True)
class DemoAccount:
    """A Keycloak user the mock login page accepts."""

    login: str
    password: str
    member_id: str
    name: str


DEMO_ACCOUNTS: Final[tuple[DemoAccount, ...]] = (
    DemoAccount("champion", DEMO_PASSWORD, "FSP-100101", "Анна Соколова"),
    DemoAccount("cup", DEMO_PASSWORD, "FSP-100202", "Илья Морозов"),
    DemoAccount("hackathon", DEMO_PASSWORD, "FSP-100303", "Мария Лебедева"),
    DemoAccount("empty", DEMO_PASSWORD, NO_HISTORY_ID, "Пётр Новиков"),
    DemoAccount("offline", DEMO_PASSWORD, REGISTRY_DOWN_ID, "Ольга Сергеева"),
)
DEMO_MEMBERS: Final = tuple(account.member_id for account in DEMO_ACCOUNTS)


def account_by_login(login: str) -> DemoAccount | None:
    key = login.strip().casefold()
    return next((account for account in DEMO_ACCOUNTS if account.login == key), None)


def account_by_member(member_id: str) -> DemoAccount | None:
    return next((account for account in DEMO_ACCOUNTS if account.member_id == member_id), None)


def password_matches(given: str, expected: str) -> bool:
    return secrets.compare_digest(given.encode(), expected.encode())


def display_name(member_id: str) -> str:
    account = account_by_member(member_id)
    return account.name if account is not None else f"Участник {member_id}"


def _key(settings: Settings) -> str:
    secret = settings.jwt_secret.get_secret_value().encode("utf-8")
    return hashlib.sha256(b"fsp-mock-idp:" + secret).hexdigest()


def _issuer(settings: Settings) -> str:
    return settings.fsp_id_issuer.rstrip("/")


def subject_of(member_id: str) -> str:
    """Stable Keycloak-like user id of a participant."""
    return str(uuid.uuid5(_SUBJECTS, member_id))


# --- FSP ID ---------------------------------------------------------------------------------------


def issue_code(
    settings: Settings,
    *,
    member_id: str,
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    nonce: str,
) -> str:
    """The authorization code: self-contained, so the emulation needs no storage."""
    now = datetime.now(UTC)
    payload = {
        "iss": _issuer(settings),
        "typ": _CODE_TYPE,
        "sub": member_id,
        "aud": client_id,
        "ru": redirect_uri,
        "cc": code_challenge,
        "nonce": nonce,
        "iat": now,
        "exp": now + CODE_TTL,
    }
    return jwt.encode(payload, _key(settings), algorithm=_ALGORITHM)


def redeem_code(
    settings: Settings, *, code: str, client_id: str, redirect_uri: str, code_verifier: str
) -> dict[str, Any]:
    """The token endpoint: checks the code like Keycloak does and answers with the tokens."""
    try:
        claims = jwt.decode(
            code,
            _key(settings),
            algorithms=[_ALGORITHM],
            audience=client_id,
            issuer=_issuer(settings),
            options={"require": ["exp", "sub", "aud", "iss"]},
        )
    except jwt.InvalidTokenError as exc:
        raise FspIdError("ФСП ID: код входа недействителен или устарел") from exc
    if claims.get("typ") != _CODE_TYPE or claims.get("ru") != redirect_uri:
        raise FspIdError("ФСП ID: код входа выдан для другого адреса")
    if claims.get("cc") != provider.code_challenge(code_verifier):
        raise FspIdError("ФСП ID: проверка PKCE не пройдена")

    member_id = str(claims["sub"])
    now = datetime.now(UTC)
    common = {
        "iss": _issuer(settings),
        "sub": subject_of(member_id),
        "iat": now,
        "exp": now + TOKEN_TTL,
        MEMBER_CLAIM: member_id,
    }
    id_token = jwt.encode(
        {
            **common,
            "aud": client_id,
            "azp": client_id,
            "nonce": claims.get("nonce"),
            "name": display_name(member_id),
        },
        _key(settings),
        algorithm=_ALGORITHM,
    )
    access_token = jwt.encode(
        {**common, "typ": _ACCESS_TYPE, "azp": client_id, "scope": SCOPES},
        _key(settings),
        algorithm=_ALGORITHM,
    )
    return {
        "access_token": access_token,
        "id_token": id_token,
        "token_type": "Bearer",
        "expires_in": int(TOKEN_TTL.total_seconds()),
        "scope": SCOPES,
    }


def userinfo(settings: Settings, access_token: str) -> dict[str, Any]:
    try:
        claims = jwt.decode(
            access_token, _key(settings), algorithms=[_ALGORITHM], issuer=_issuer(settings)
        )
    except jwt.InvalidTokenError as exc:
        raise FspIdError("ФСП ID: токен доступа недействителен") from exc
    if claims.get("typ") != _ACCESS_TYPE:
        raise FspIdError("ФСП ID: токен доступа недействителен")
    member_id = str(claims[MEMBER_CLAIM])
    return {"sub": claims["sub"], MEMBER_CLAIM: member_id, "name": display_name(member_id)}


class MockFspIdProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def authorize_url(
        self, *, state: str, nonce: str, code_challenge: str, redirect_uri: str
    ) -> str:
        return provider.authorize_url(
            self._settings,
            state=state,
            nonce=nonce,
            code_challenge=code_challenge,
            redirect_uri=redirect_uri,
        )

    async def exchange_code(
        self, *, code: str, code_verifier: str, redirect_uri: str, nonce: str
    ) -> FspIdentity:
        settings = self._settings
        tokens = redeem_code(
            settings,
            code=code,
            client_id=settings.fsp_id_client_id,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
        )
        try:
            claims = jwt.decode(
                tokens["id_token"],
                _key(settings),
                algorithms=[_ALGORITHM],
                audience=settings.fsp_id_client_id,
            )
        except jwt.InvalidTokenError as exc:
            raise FspIdError("ФСП ID вернул некорректный ID-токен") from exc
        return provider.identity_from_claims(claims, settings=settings, nonce=nonce)


# --- registry -------------------------------------------------------------------------------------


def fixture_record(candidate: CandidateFixture) -> FspMemberRecord:
    if candidate.fsp_member_id is None:  # pragma: no cover - callers filter these out
        msg = f"{candidate.key} has no FSP ID"
        raise ValueError(msg)
    return FspMemberRecord(
        member_id=candidate.fsp_member_id,
        achievements=[
            FspRegistryAchievement.model_validate(item.model_dump())
            for item in candidate.fsp_achievements
        ],
        titles=[
            FspRegistryTitle.model_validate(item.model_dump()) for item in candidate.fsp_titles
        ],
    )


@lru_cache(maxsize=1)
def seeded_members() -> dict[str, FspMemberRecord]:
    """The demo profiles' histories, so a re-sync of a demo account changes nothing."""
    return {
        candidate.fsp_member_id: fixture_record(candidate)
        for candidate in load_seed_data().candidates
        if candidate.fsp_member_id is not None
    }


_GENERATED_EVENTS: Final[tuple[tuple[str, FspEventKind, FspEventLevel], ...]] = (
    (content.FSP_NATIONAL_EVENTS[0], FspEventKind.CHAMPIONSHIP, FspEventLevel.NATIONAL),
    (content.FSP_NATIONAL_EVENTS[1], FspEventKind.CUP, FspEventLevel.NATIONAL),
    (content.FSP_OLYMPIAD_EVENT, FspEventKind.OLYMPIAD, FspEventLevel.NATIONAL),
    (
        content.FSP_HACKATHON_EVENTS[FspDiscipline.PRODUCT][0],
        FspEventKind.HACKATHON,
        FspEventLevel.NATIONAL,
    ),
    ("Международный хакатон ФСП", FspEventKind.HACKATHON, FspEventLevel.INTERNATIONAL),
    (
        "Чемпионат Томской области по спортивному программированию",
        FspEventKind.CHAMPIONSHIP,
        FspEventLevel.REGIONAL,
    ),
    (
        "Кубок Новосибирской области по спортивному программированию",
        FspEventKind.CUP,
        FspEventLevel.REGIONAL,
    ),
)
_PLACES: Final = (1, 2, 3, 5, 8, 12, None, None)


def generated_member(member_id: str) -> FspMemberRecord:
    """A plausible history for any id, the same on every call."""
    rng = random.Random(zlib.crc32(member_id.encode("utf-8")))  # noqa: S311 - demo data
    achievements: list[FspRegistryAchievement] = []
    for index in range(rng.randint(1, 4)):
        event_name, kind, level = rng.choice(_GENERATED_EVENTS)
        discipline = (
            FspDiscipline.PRODUCT
            if kind == FspEventKind.HACKATHON
            else rng.choice(list(FspDiscipline))
        )
        place = rng.choice(_PLACES)
        team = kind == FspEventKind.HACKATHON or rng.random() < content.FSP_TEAM_SHARE[discipline]
        achievements.append(
            FspRegistryAchievement(
                id=f"ach-{member_id}-{index + 1}",
                event_name=event_name,
                event_kind=kind,
                discipline=discipline,
                level=level,
                year=rng.randint(2022, 2026),
                place=place,
                result=FspOutcome.from_place(place),
                participation=FspParticipation.TEAM if team else FspParticipation.INDIVIDUAL,
                team_name=rng.choice(content.FSP_TEAM_NAMES) if team else None,
            )
        )
    achievements.sort(key=lambda item: (-item.year, item.place or 99))
    titles: list[FspRegistryTitle] = []
    podium = [item for item in achievements if item.place is not None and item.place <= 3]  # noqa: PLR2004
    if podium:
        best = podium[0]
        national = best.level != FspEventLevel.REGIONAL
        titles.append(
            FspRegistryTitle(
                id=f"ttl-{member_id}-1",
                kind=FspTitleKind.KMS if national else FspTitleKind.RANK_1,
                discipline=best.discipline,
                awarded_year=best.year,
            )
        )
    return FspMemberRecord(member_id=member_id, achievements=achievements, titles=titles)


def random_member_id() -> str:
    """A participant nobody has linked yet, with a generated history."""
    taken = {*DEMO_MEMBERS, *seeded_members()}
    while True:
        member_id = f"FSP-{secrets.randbelow(900_000) + 100_000}"
        if member_id not in taken:
            return member_id


class MockFspRegistry:
    async def fetch_member(self, member_id: str) -> FspMemberRecord:
        return member_record(member_id)


def member_record(member_id: str) -> FspMemberRecord:
    if member_id == REGISTRY_DOWN_ID:
        raise FspRegistryError()
    if member_id == NO_HISTORY_ID:
        return FspMemberRecord(member_id=member_id)
    return seeded_members().get(member_id) or generated_member(member_id)
